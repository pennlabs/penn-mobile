import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from presence.models import Venue
from presence.serializers import VenueImportSerializer


class Command(BaseCommand):
    help = "Import venue definitions atomically without creating dining sources or fitness rooms."

    def add_arguments(self, parser):
        default = Path(__file__).resolve().parents[2] / "data" / "tracked_locations.json"
        parser.add_argument("file", nargs="?", default=str(default))
        parser.add_argument(
            "--dry-run", action="store_true", help="Validate without saving changes."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with open(options["file"]) as source:
                records = json.load(source)
        except (OSError, ValueError) as error:
            raise CommandError(f"Cannot read venue configuration: {error}")
        if not isinstance(records, list):
            raise CommandError("Venue configuration must be a JSON array.")
        identifiers, dining_sources, plans = set(), set(), []
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("venue_id"), str):
                raise CommandError("Each venue must be an object with a venue_id.")
            venue_id = record["venue_id"]
            if venue_id in identifiers:
                raise CommandError(f"Duplicate venue_id: {venue_id}")
            identifiers.add(venue_id)
            venue = Venue.objects.select_for_update().filter(pk=venue_id).first()
            is_new = venue is None
            serializer = VenueImportSerializer(instance=venue, data=record, partial=not is_new)
            if not serializer.is_valid():
                raise CommandError(f"{venue_id}: {serializer.errors}")
            data = dict(serializer.validated_data)
            rooms = data.pop("fitness_room_names", None)
            venue = venue or Venue()
            changed = any(getattr(venue, field) != value for field, value in data.items())
            rooms_changed = rooms is not None and (
                is_new
                or set(venue.fitness_rooms.values_list("pk", flat=True))
                != {room.pk for room in rooms}
            )
            changed |= rooms_changed
            for field, value in data.items():
                setattr(venue, field, value)
            if venue.dining_venue_id is not None:
                if venue.dining_venue_id in dining_sources:
                    raise CommandError("Each dining source can belong to only one presence venue.")
                dining_sources.add(venue.dining_venue_id)
            if not is_new and rooms is None and venue.kind != Venue.Kind.GYM:
                if venue.fitness_rooms.exists():
                    raise CommandError(
                        f"{venue_id}: Clear fitness_room_names before changing kind."
                    )
            try:
                venue.full_clean()
            except ValidationError as error:
                raise CommandError(f"{venue_id}: {error.message_dict}")
            if not is_new and changed:
                venue.configuration_version += 1
            plans.append((venue, rooms if rooms_changed else None, is_new or changed))
        if not options["dry_run"]:
            try:
                for venue, rooms, save in plans:
                    if save:
                        venue.save()
                    if rooms is not None:
                        venue.fitness_rooms.set(rooms)
            except IntegrityError as error:
                raise CommandError(f"Conflicting venue/source references: {error}")
        action = "Validated" if options["dry_run"] else "Imported"
        self.stdout.write(self.style.SUCCESS(f"{action} {len(plans)} venues."))
