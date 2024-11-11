from typing import Any, Dict, TypeAlias

from django.db.models import Manager, QuerySet

from sublet.models import Amenity, Offer, Sublet, SubletImage


# QuerySet types
SubletQuerySet: TypeAlias = QuerySet[Sublet, Manager[Sublet]]
OfferQuerySet: TypeAlias = QuerySet[Offer, Manager[Offer]]
AmenityQuerySet: TypeAlias = QuerySet[Amenity, Manager[Amenity]]
ImageList: TypeAlias = QuerySet[SubletImage, Manager[SubletImage]]
UserOfferQuerySet: TypeAlias = QuerySet[Offer, Manager[Offer]]

# Data structure types
ValidationData: TypeAlias = Dict[str, Any]
