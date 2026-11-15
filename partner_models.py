""" Profitability and Cost models

Activating Virtual Environment: # source .venv/bin/activate

Values we need for each partner (can add as many partners as you like):
    - name/type of partner
    - Low/medium/high estimates of the number of EVs served per year
    - kWh delivered per EV (annually)
    - Annual fixed cost
    - Cost per kWh
    - Revenue per kWh

"""

from dataclasses import dataclass
from math import ceil

import matplotlib.pyplot as plt


@dataclass
class Scenario:
    name: str
    evs_served_per_year: int
    kwh_per_ev_per_year: float

    def annual_kwh(self) -> float:
        return self.evs_served_per_year * self.kwh_per_ev_per_year


@dataclass
class Partner:
    name: str
    partner_type: str
    annual_fixed_cost: float
    cost_per_kwh: float
    revenue_per_kwh: float
    scenarios: list[Scenario]
    location_type: str = "medium"


ASSUMED_KWH_PER_SESSION = 20

BASE_FIXED_COST = 10000
location_multipliers = {'small' : 0.75, 'medium' : 1, 'large' : 1.25}
def fixed_cost_multiplier(partner : Partner) -> float:
    return BASE_FIXED_COST * location_multipliers[partner.location_type]


def annual_revenue(partner: Partner, kwh: float) -> float:
    return kwh * partner.revenue_per_kwh


def annual_cost(partner: Partner, kwh: float) -> float:
    return partner.annual_fixed_cost + kwh * partner.cost_per_kwh


def annual_profit(partner: Partner, kwh: float) -> float:
    return annual_revenue(partner, kwh) - annual_cost(partner, kwh)

partners = [
    Partner(
        name="Northeastern University",
        partner_type="University",
        location_type = "small",
        annual_fixed_cost=18_000,
        cost_per_kwh=13 / ASSUMED_KWH_PER_SESSION,
        revenue_per_kwh=25 / ASSUMED_KWH_PER_SESSION,
        scenarios=[
            Scenario("Low", evs_served_per_year=40, kwh_per_ev_per_year=18 * ASSUMED_KWH_PER_SESSION),
            Scenario("Medium", evs_served_per_year=100, kwh_per_ev_per_year=18 * ASSUMED_KWH_PER_SESSION),
            Scenario("High", evs_served_per_year=160, kwh_per_ev_per_year=18 * ASSUMED_KWH_PER_SESSION),
        ],
    ),
    Partner(
        name="Avalon North Station",
        partner_type="Residential property",
        location_type = "large",
        annual_fixed_cost=12_000,
        cost_per_kwh=15 / ASSUMED_KWH_PER_SESSION,
        revenue_per_kwh=25 / ASSUMED_KWH_PER_SESSION,
        scenarios=[
            Scenario("Low", evs_served_per_year=25, kwh_per_ev_per_year=12 * ASSUMED_KWH_PER_SESSION),
            Scenario("Medium", evs_served_per_year=50, kwh_per_ev_per_year=12 * ASSUMED_KWH_PER_SESSION),
            Scenario("High", evs_served_per_year=100, kwh_per_ev_per_year=12 * ASSUMED_KWH_PER_SESSION),
        ],
    ),
]

max_kwh = max(scenario.annual_kwh() for partner in partners for scenario in partner.scenarios)

kwh_range = [0, max(1, ceil(max_kwh * 1.1))]

fig, (cost_ax, profit_ax) = plt.subplots(1, 2, figsize=(13, 5))

for partner in partners:
    costs = [annual_cost(partner, kwh) for kwh in kwh_range]
    profits = [annual_profit(partner, kwh) for kwh in kwh_range]

    cost_line, = cost_ax.plot(kwh_range, costs, label=partner.name)
    color = cost_line.get_color()
    profit_ax.plot(kwh_range, profits, label=partner.name, color=color)

    print(f"\n{partner.name} | {partner.partner_type}")

    for scenario in partner.scenarios:
        kwh = scenario.annual_kwh()
        revenue = annual_revenue(partner, kwh)
        cost = annual_cost(partner, kwh)
        profit = annual_profit(partner, kwh)

        cost_ax.scatter(kwh, cost, color=color, zorder=3)
        profit_ax.scatter(kwh, profit, color=color, zorder=3)
        profit_ax.annotate(
            scenario.name,
            (kwh, profit),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

        print(
            f"  {scenario.name:6} | {kwh:,.1f} kWh | "
            f"Revenue ${revenue:,.2f} | Cost ${cost:,.2f} | "
            f"Profit ${profit:,.2f}"
        )

cost_ax.set(
    title="Annual cost to SparkCharge",
    xlabel="Energy delivered per year (kWh)",
    ylabel="Annual cost ($)",
)
profit_ax.set(
    title="Annual profit for SparkCharge",
    xlabel="Energy delivered per year (kWh)",
    ylabel="Annual profit ($)",
)
profit_ax.axhline(0, color="gray", linestyle="--", linewidth=1, label='Break Even')
cost_ax.legend(fontsize=8)
profit_ax.legend(fontsize=8)

fig.tight_layout()
plt.show()