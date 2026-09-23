from rest_framework import permissions

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