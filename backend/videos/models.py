from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField()
    analysis_result = models.JSONField(null=True, blank=True)
    summary_result = models.TextField(null=True, blank=True)
    fire_evaluation = models.JSONField(null=True, blank=True)
    assault_evaluation = models.JSONField(null=True, blank=True)
    crime_evaluation = models.JSONField(null=True, blank=True)
    drug_evaluation = models.JSONField(null=True, blank=True)
    theft_evaluation = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
