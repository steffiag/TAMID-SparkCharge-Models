""" Profitability and Cost models

Activating Virtual Environment: # source .venv/bin/activate

Values we need for each partner (can add as many partners as you like):
    - name/type of partner
    - Low/medium/high estimates of the number of EVs served per year
    - Sessions per EV (annually)
    - Annual fixed cost
    - Costs per session
    - Revenue per session

"""

from dataclasses import dataclass
from math import ceil

import matplotlib.pyplot as plt


@dataclass
class Scenario:
    name: str
    evs_served_per_year: int
    sessions_per_ev_per_year: float

    def annual_sessions(self) -> float:
        return self.evs_served_per_year * self.sessions_per_ev_per_year


@dataclass
class Partner:
    name: str
    partner_type: str
    annual_fixed_cost: float
    cost_per_session: float
    revenue_per_session: float
    scenarios: list[Scenario]


def annual_revenue(partner: Partner, sessions: float) -> float:
    return sessions * partner.revenue_per_session


def annual_cost(partner: Partner, sessions: float) -> float:
    return partner.annual_fixed_cost + sessions * partner.cost_per_session


def annual_profit(partner: Partner, sessions: float) -> float:
    return annual_revenue(partner, sessions) - annual_cost(partner, sessions)

partners = [
    Partner(
        name="Northeastern University",
        partner_type="University",
        annual_fixed_cost=18_000,
        cost_per_session=13,
        revenue_per_session=25,
        scenarios=[
            Scenario("Low", evs_served_per_year=40, sessions_per_ev_per_year=18),
            Scenario("Medium", evs_served_per_year=100, sessions_per_ev_per_year=18),
            Scenario("High", evs_served_per_year=160, sessions_per_ev_per_year=18),
        ],
    ),
    Partner(
        name="Avalon North Station",
        partner_type="Residential property",
        annual_fixed_cost=12_000,
        cost_per_session=15,
        revenue_per_session=25,
        scenarios=[
            Scenario("Low", evs_served_per_year=25, sessions_per_ev_per_year=12),
            Scenario("Medium", evs_served_per_year=50, sessions_per_ev_per_year=12),
            Scenario("High", evs_served_per_year=100, sessions_per_ev_per_year=12),
        ],
    ),
]

max_sessions = max(scenario.annual_sessions() for partner in partners for scenario in partner.scenarios)

session_range = [0, max(1, ceil(max_sessions * 1.1))]

fig, (cost_ax, profit_ax) = plt.subplots(1, 2, figsize=(13, 5))

for partner in partners:
    costs = [annual_cost(partner, sessions) for sessions in session_range]
    profits = [annual_profit(partner, sessions) for sessions in session_range]

    cost_line, = cost_ax.plot(session_range, costs, label=partner.name)
    color = cost_line.get_color()
    profit_ax.plot(session_range, profits, label=partner.name, color=color)

    print(f"\n{partner.name} | {partner.partner_type}")

    for scenario in partner.scenarios:
        sessions = scenario.annual_sessions()
        revenue = annual_revenue(partner, sessions)
        cost = annual_cost(partner, sessions)
        profit = annual_profit(partner, sessions)

        cost_ax.scatter(sessions, cost, color=color, zorder=3)
        profit_ax.scatter(sessions, profit, color=color, zorder=3)
        profit_ax.annotate(
            scenario.name,
            (sessions, profit),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

        print(
            f"  {scenario.name:6} | {sessions:,.1f} sessions | "
            f"Revenue ${revenue:,.2f} | Cost ${cost:,.2f} | "
            f"Profit ${profit:,.2f}"
        )

cost_ax.set(
    title="Annual cost to SparkCharge",
    xlabel="Charging sessions per year",
    ylabel="Annual cost ($)",
)
profit_ax.set(
    title="Annual profit for SparkCharge",
    xlabel="Charging sessions per year",
    ylabel="Annual profit ($)",
)
profit_ax.axhline(0, color="gray", linestyle="--", linewidth=1)
cost_ax.legend(fontsize=8)
profit_ax.legend(fontsize=8)

fig.tight_layout()
plt.show()