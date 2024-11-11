from typing import Any, Dict, List, TypeAlias

from django.db.models import Manager, QuerySet

from portal.models import Poll, PollOption, PollVote, Post, TargetPopulation


# QuerySet types
PollQuerySet: TypeAlias = QuerySet[Poll, Manager[Poll]]
PostQuerySet: TypeAlias = QuerySet[Post, Manager[Post]]
PollVoteQuerySet: TypeAlias = QuerySet[PollVote, Manager[PollVote]]
PollOptionQuerySet: TypeAlias = QuerySet[PollOption, Manager[PollOption]]

# Data structure types
VoteStatistics: TypeAlias = Dict[str, Any]
ClubCode: TypeAlias = str
ValidationData: TypeAlias = Dict[str, Any]

# Population types
PopulationList: TypeAlias = List[TargetPopulation]
PopulationGroups: TypeAlias = List[PopulationList]
