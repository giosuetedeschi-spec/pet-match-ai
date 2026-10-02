import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import Comune


REQUIRED_COLUMNS = {
    'istat_code', 'name', 'province_code', 'province', 'province_abbreviation',
    'region', 'latitude', 'longitude',
}


class Command(BaseCommand):
    help = 'Import or refresh the official ISTAT municipality reference data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=Path,
            default=settings.BASE_DIR / 'data' / 'comuni_istat_2026.csv',
            help='Path to a normalized ISTAT municipality CSV.',
        )

    def handle(self, *args, **options):
        source = options['file']
        try:
            with source.open(encoding='utf-8-sig', newline='') as input_file:
                reader = csv.DictReader(input_file)
                if not REQUIRED_COLUMNS.issubset(reader.fieldnames or ()):
                    raise CommandError(f'{source} is missing required municipality columns.')
                rows = [self._make_comune(row, source) for row in reader]
        except OSError as error:
            raise CommandError(f'Cannot read {source}: {error}') from error

        codes = [comune.istat_code for comune in rows]
        if not rows or len(codes) != len(set(codes)):
            raise CommandError(f'{source} must contain municipalities with unique ISTAT codes.')

        with transaction.atomic():
            Comune.objects.bulk_create(
                rows,
                batch_size=500,
                update_conflicts=True,
                update_fields=(
                    'name', 'province_code', 'province', 'province_abbreviation',
                    'region', 'latitude', 'longitude',
                ),
                unique_fields=('istat_code',),
            )
            incoming = set(codes)
            existing = Comune.objects.values_list('istat_code', flat=True)
            stale = [code for code in existing if code not in incoming]
            for start in range(0, len(stale), 500):
                Comune.objects.filter(istat_code__in=stale[start:start + 500]).delete()

        self.stdout.write(self.style.SUCCESS(f'Imported {len(rows)} municipalities; removed {len(stale)} obsolete records.'))

    @staticmethod
    def _make_comune(row, source):
        code = (row.get('istat_code') or '').strip()
        name = (row.get('name') or '').strip()
        if len(code) != 6 or not code.isdigit() or not name:
            raise CommandError(f'{source} contains an invalid ISTAT code or municipality name.')
        try:
            latitude = Decimal(row['latitude'])
            longitude = Decimal(row['longitude'])
        except (InvalidOperation, KeyError) as error:
            raise CommandError(f'{source} contains invalid coordinates for {code}.') from error
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise CommandError(f'{source} contains out-of-range coordinates for {code}.')

        return Comune(
            istat_code=code,
            name=name,
            province_code=(row.get('province_code') or '').strip(),
            province=(row.get('province') or '').strip(),
            province_abbreviation=(row.get('province_abbreviation') or '').strip(),
            region=(row.get('region') or '').strip(),
            latitude=latitude,
            longitude=longitude,
            postal_codes=[],
        )
