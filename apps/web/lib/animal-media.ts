import sharp from "sharp";

export const maxPhotoBytes = 10 * 1024 * 1024;
export const maxPhotosPerAnimal = 10;

export async function processAnimalPhoto(input: Buffer) {
  const image = sharp(input, { limitInputPixels: 40_000_000 }).rotate();
  const metadata = await image.metadata();
  if (!metadata.width || !metadata.height || !["jpeg", "png", "webp", "heif", "avif"].includes(metadata.format ?? "")) {
    throw new Error("Formato foto non supportato. Usa JPEG, PNG, WebP o HEIC.");
  }
  if (metadata.width * metadata.height > 40_000_000 || (metadata.pages ?? 1) > 1) {
    throw new Error("La foto supera la risoluzione consentita o contiene più fotogrammi.");
  }

  const original = await image
    .resize({ width: 4096, height: 4096, fit: "inside", withoutEnlargement: true })
    .webp({ quality: 88 })
    .toBuffer({ resolveWithObject: true });
  const variants = new Map<string, Buffer>([["original.webp", original.data]]);
  for (const width of [320, 640, 1280, 1920]) {
    const variant = await sharp(original.data).resize({ width, withoutEnlargement: true }).webp({ quality: 82 }).toBuffer();
    variants.set(`${width}.webp`, variant);
  }
  return {
    width: original.info.width,
    height: original.info.height,
    byteSize: original.data.byteLength,
    variants,
  };
}
