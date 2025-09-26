from django.db import models

# Create your models here.

from django.conf import settings

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    # optional: simple role field
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_lawyer = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({'Lawyer' if self.is_lawyer else 'Client'})"

class Consultation(models.Model):
    """
    A consultation room connecting one lawyer and one client.
    Room name will be "consult-<id>"
    """
    lawyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lawyer_consultations")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client_consultations")
    created_at = models.DateTimeField(auto_now_add=True)
    topic = models.CharField(max_length=255, blank=True)

    def room_name(self):
        return f"consult-{self.pk}"

    def __str__(self):
        return f"Consult {self.pk}: {self.lawyer} <> {self.client}"

class Message(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ("timestamp",)

    def __str__(self):
        return f"{self.sender}: {self.content[:30]}"
