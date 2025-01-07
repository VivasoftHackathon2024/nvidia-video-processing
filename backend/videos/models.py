from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField()
    analysis_result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
