from django.db import models
from slugify import slugify


def generate_unique_slug(
    instance: models.Model,
    source_text: str,
    slug_field_name: str = "slug",
    fallback_slug: str = "item",
) -> str:
    """
    Generates a unique slug for a given model instance using python-slugify.
    Handles collision resolution by appending '-1', '-2', etc.
    """
    base_slug = slugify(source_text) or fallback_slug
    slug = base_slug
    counter = 1

    model_class: type[models.Model] = instance.__class__

    queryset = model_class._default_manager.filter(**{slug_field_name: slug})

    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
        queryset = model_class._default_manager.filter(**{slug_field_name: slug})
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)

    return slug
