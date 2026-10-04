from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Competition(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Season(models.Model):
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name="seasons"
    )
    name = models.CharField(max_length=20)

    class Meta:
        unique_together = ("competition", "name")

    def __str__(self):
        return f"{self.competition.name} {self.name}"


class Match(models.Model):
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name="matches"
    )
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="matches"
    )

    date = models.DateTimeField()

    home_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="home_matches"
    )
    away_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="away_matches"
    )
    fixture_id = models.IntegerField(
        null = True,
        blank = True, 
        unique = True
    )

    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)
    home_shots_on_goal = models.IntegerField(null=True, blank=True)
    away_shots_on_goal = models.IntegerField(null=True, blank=True)

    home_shots_off_goal = models.IntegerField(null=True, blank=True)
    away_shots_off_goal = models.IntegerField(null=True, blank=True)

    home_total_shots = models.IntegerField(null=True, blank=True)
    away_total_shots = models.IntegerField(null=True, blank=True)

    home_corners = models.IntegerField(null=True, blank=True)
    away_corners = models.IntegerField(null=True, blank=True)

    home_possession = models.IntegerField(null=True, blank=True)
    away_possession = models.IntegerField(null=True, blank=True)

    home_goalkeeper_saves = models.IntegerField(null=True, blank=True)
    away_goalkeeper_saves = models.IntegerField(null=True, blank=True)

    home_fouls = models.IntegerField(null=True, blank=True)
    away_fouls = models.IntegerField(null=True, blank=True)

    home_offsides = models.IntegerField(null=True, blank=True)
    away_offsides = models.IntegerField(null=True, blank=True)

    home_yellow_cards = models.IntegerField(null=True, blank=True)
    away_yellow_cards = models.IntegerField(null=True, blank=True)

    home_red_cards = models.IntegerField(null=True, blank=True)
    away_red_cards = models.IntegerField(null=True, blank=True)

    stage = models.CharField(max_length=50)

    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.home_team} - {self.away_team}"

class TeamElo(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="elo_ratings"
    )
    date = models.DateField()
    elo = models.FloatField()

    class Meta:
        unique_together = ("team", "date")

    def __str__(self):
        return f"{self.team.name} - {self.date}: {self.elo}"
