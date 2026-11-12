"""
Tournament Bracket - a Drafter website for running a four-team,
single-elimination sports tournament.

Enter four teams, pick the winner of each semifinal, then pick the
champion of the final.

Run with:  python tournament_bracket.py
"""
from dataclasses import dataclass
from drafter import *

# Global constants
SEMIFINAL_ROUND = 1
CHAMPIONSHIP_ROUND = 2
DEFAULT_TOURNAMENT_NAME = "My Tournament"

@dataclass
class Team:
    """One team in the tournament."""
    name: str
    winner: bool    # True if the team won its most recent game

@dataclass
class State:
    """Everything the website remembers between pages."""
    teams: list[Team]          
    round_number: int          
    champion: str              
    tournament_started: bool   
    tournament_name: str       

# Helper functions
def all_names_entered(names: list[str]) -> bool:
    """Return True only if every name in the list is non-empty."""
    for name in names:
        if name == "":
            return False
    return True


def has_duplicate_names(names: list[str]) -> bool:
    """Return True if two teams share a name (ignoring capital letters)."""
    seen = []
    for name in names:
        if name.lower() in seen:
            return True
        seen.append(name.lower())
    return False


def entry_content(error: str) -> list:
    """Build the team entry form. `error` is shown at the top if not empty."""
    content = [Header("Enter Your Teams")]
    if error != "":
        content.append(Text(error))
    content.extend([
        "Tournament name:",
        TextBox("tournament_name", DEFAULT_TOURNAMENT_NAME),
        "Team 1:",
        TextBox("team1", ""),
        "Team 2:",
        TextBox("team2", ""),
        "Team 3:",
        TextBox("team3", ""),
        "Team 4:",
        TextBox("team4", ""),
        Button("Generate matchups", generate_matchups),
        Button("Back to home", index),
    ])
    return content

# Routes
@route
def index(state: State) -> Page:
    """Home page: start a tournament or read the instructions."""
    content = [Header("Tournament Bracket Maker")]
    if state.champion != "":
        content.append(Text(f"Last champion: {state.champion}"))
    content.extend([
        Text("Build a four-team bracket and crown a champion."),
        Button("Start tournament", team_entry),
        Button("View instructions", instructions),
    ])
    return Page(state, content)


@route
def instructions(state: State) -> Page:
    """Page explaining how the site works."""
    return Page(state, [
        Header("How It Works"),
        "1. Press Start tournament and enter a tournament name and four teams.",
        "2. The site pairs Team 1 vs Team 2 and Team 3 vs Team 4.",
        "3. Choose the winner of each matchup and submit.",
        "4. The two winners meet in the championship.",
        "5. Choose the champion to finish the tournament.",
        "6. Press New tournament to start over.",
        Button("Back to home", index),
    ])


@route
def team_entry(state: State) -> Page:
    """Page where the user enters the tournament name and four team names."""
    return Page(state, entry_content(""))


@route
def generate_matchups(state: State, tournament_name: str, team1: str,
                      team2: str, team3: str, team4: str) -> Page:
    """Check the entries; if they are valid, build the teams and show matchups."""
    names = [team1.strip(), team2.strip(), team3.strip(), team4.strip()]

    if not all_names_entered(names):
        return Page(state, entry_content("Please enter all four team names."))
    if has_duplicate_names(names):
        return Page(state, entry_content("Each team needs a different name."))

    state.teams = []
    for name in names:
        state.teams.append(Team(name, False))

    if tournament_name.strip() == "":
        state.tournament_name = DEFAULT_TOURNAMENT_NAME
    else:
        state.tournament_name = tournament_name.strip()
    state.round_number = SEMIFINAL_ROUND
    state.champion = ""
    state.tournament_started = True
    return matchups(state)


@route
def matchups(state: State) -> Page:
    """Show the semifinal matchups and let the user pick each winner."""
    if not state.tournament_started:
        return Page(state, [
            Header("No tournament yet"),
            Text("Start a tournament first."),
            Button("Back to home", index),
        ])

    content = [
        Header(f"{state.tournament_name}: Semifinals"),
        Text("Teams in the tournament:"),
    ]
    for team in state.teams:
        content.append(Text("- " + team.name))

    if state.round_number >= CHAMPIONSHIP_ROUND:
        content.append(Text("The semifinals are finished."))
        content.append(Button("Go to championship", championship))
    else:
        first, second, third, fourth = state.teams
        content.extend([
            Text(f"Game 1: {first.name} vs {second.name}"),
            SelectBox("winner1", [first.name, second.name], first.name),
            Text(f"Game 2: {third.name} vs {fourth.name}"),
            SelectBox("winner2", [third.name, fourth.name], third.name),
            Button("Submit winners", record_winners),
        ])
    content.append(Button("Back to home", index))
    return Page(state, content)


@route
def record_winners(state: State, winner1: str, winner2: str) -> Page:
    """Mark the two semifinal winners and move on to the championship."""
    for team in state.teams:
        team.winner = (team.name == winner1 or team.name == winner2)
    state.round_number = CHAMPIONSHIP_ROUND
    return championship(state)


@route
def championship(state: State) -> Page:
    """Show the championship matchup, or the champion once it is decided."""
    if not state.tournament_started or state.round_number < CHAMPIONSHIP_ROUND:
        return matchups(state)

    if state.champion != "":
        return Page(state, [
            Header(f"{state.tournament_name}: Champion"),
            Text(f"{state.champion} wins the tournament!"),
            Button("New tournament", new_tournament),
            Button("Back to home", index),
        ])

    finalists = []
    for team in state.teams:
        if team.winner:
            finalists.append(team.name)  
    if len(finalists) != 2:
        return Page(state, [
            Header("Error"),
            Text("There should be exactly two finalists."),
            Button("Back to matchups", matchups)
        ])

    return Page(state, [
        Header(f"{state.tournament_name}: Championship"),
        Text(f"Final: {finalists[0]} vs {finalists[1]}"),
        SelectBox("champion_name", finalists, finalists[0]),
        Button("Crown champion", declare_champion),
        Button("Back to home", index),
    ])


@route
def declare_champion(state: State, champion_name: str) -> Page:
    """Save the champion and mark only that team as the winner."""
    is_finalist = False
    for team in state.teams:
        if team.winner and team.name == champion_name:
            is_finalist = True

    if is_finalist:
        state.champion = champion_name
        for team in state.teams:
            team.winner = (team.name == champion_name)
    return championship(state)


@route
def new_tournament(state: State) -> Page:
    """Reset the tournament so a new one can be started."""
    state.teams = []
    state.round_number = 0
    state.champion = ""
    state.tournament_started = False
    state.tournament_name = ""
    return team_entry(state)


start_server(State([], 0, "", False, ""))
