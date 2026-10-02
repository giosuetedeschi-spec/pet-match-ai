from rest_framework import permissions

class IsApprovedShelter(permissions.BasePermission):
    message = 'Il rifugio deve essere approvato prima di pubblicare animali.'

    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated
            and user.role == 'SHELTER'
            and hasattr(user, 'shelter_profile')
            and user.shelter_profile.is_verified
        )


class IsShelterOwnerOfAnimal(permissions.BasePermission):
    """
    Permesso personalizzato: concede accesso di modifica soltanto se l'utente
    è un Rifugio ed è il proprietario dell'animale specificato.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'SHELTER'

    def has_object_permission(self, request, view, obj):
        # Se l'oggetto è AnimalImage, controlla la relazione con shelter
        if hasattr(obj, 'animal'):
            return obj.animal.shelter.user == request.user
        # Se l'oggetto è direttamente Animal
        return obj.shelter.user == request.user


from rest_framework import permissions


class IsAdopterUser(permissions.BasePermission):
    """
    Permesso personalizzato: consente l'accesso solo agli utenti autenticati con ruolo ADOPTER
    e profilo adottante associato.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'ADOPTER' and
            hasattr(request.user, 'adopter_profile')
        )