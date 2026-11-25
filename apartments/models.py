from django.contrib.auth.models import AbstractUser
from django.db import models

# TODO: Fix the typo in the field name "apartament" to "apartment" in the User model and related code.
# TODO: Change class name "Complains" to "Complaint" and make the necessary migration
# TODO: Change class "Complains" connecting it to the Apartment model instead of the User model.
 
class Apartment(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    
class User(AbstractUser):
    apartament = models.ForeignKey(Apartment, on_delete=models.CASCADE,null=True, blank=True)
    def __str__(self):
        return f"{self.username} - Apartment: {self.apartament.name if self.apartament else 'None'}"

class Complains(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    complain_text = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)

    #For the status field
    STATUS = {
        "PENDING": "Pending",
        "RESOLVED": "Resolved",
        "IGNORED": "Ignored",
    }
    status = models.CharField(max_length=10, choices=STATUS, default="PENDING")

    def __str__(self):
        return f"Complain by {self.user.username} at {self.received_at}: {self.complain_text}. Status: {self.status}"

class Package(models.Model):
    apartament = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    package_name = models.CharField(max_length=50)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Package '{self.package_name}' for {self.apartament.name} received at {self.received_at}"
