from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyTarget:
    name: str
    market: str
    status: str
    careers_url: str = ""


TARGET_COMPANIES = (
    CompanyTarget("DRW", "London / Amsterdam", "greenhouse", "https://www.drw.com/work-at-drw/listings"),
    CompanyTarget("Jane Street", "London", "greenhouse", "https://www.janestreet.com/join-jane-street/open-roles/"),
    CompanyTarget("Citadel / Citadel Securities", "London", "custom", "https://www.citadelsecurities.com/careers/"),
    CompanyTarget("G-Research", "London", "custom", "https://www.gresearch.com/careers/"),
    CompanyTarget("XTX Markets", "London", "custom", "https://www.xtxmarkets.com/careers/"),
    CompanyTarget("Jump Trading", "London", "greenhouse", "https://www.jumptrading.com/careers/"),
    CompanyTarget("Two Sigma", "London", "custom", "https://www.twosigma.com/careers/"),
    CompanyTarget("Optiver", "London / Amsterdam", "greenhouse", "https://optiver.com/working-at-optiver/career-opportunities/"),
    CompanyTarget("IMC Trading", "London / Amsterdam", "greenhouse", "https://www.imc.com/eu/careers"),
    CompanyTarget("Flow Traders", "Amsterdam", "greenhouse", "https://www.flowtraders.com/careers/"),
    CompanyTarget("Millennium Management", "London", "custom", "https://www.mlp.com/careers/"),
    CompanyTarget("Man AHL", "London", "custom", "https://www.man.com/careers"),
    CompanyTarget("Point72", "London", "custom", "https://careers.point72.com/"),
    CompanyTarget("Qube Research & Technologies", "London / Amsterdam", "custom", "https://www.qube-rt.com/careers"),
    CompanyTarget("Schonfeld", "London", "custom", "https://www.schonfeld.com/careers"),
    CompanyTarget("Maven Securities", "London / Amsterdam", "custom", "https://www.maven.co.uk/careers"),
    CompanyTarget("Cubist", "London", "custom", "https://www.citadel.com/careers/"),
    CompanyTarget("Cboe", "Amsterdam", "custom", "https://careers.cboe.com/"),
    CompanyTarget("Da Vinci Derivatives", "Amsterdam", "custom", "https://davinciderivatives.com/careers/"),
    CompanyTarget("All Options", "Amsterdam", "custom", "https://www.alloptions.nl/careers/"),
    CompanyTarget("Bloomberg", "London", "custom", "https://www.bloomberg.com/company/careers/"),
    CompanyTarget("Wise", "London", "greenhouse", "https://wise.jobs/"),
    CompanyTarget("Revolut", "London", "custom", "https://www.revolut.com/careers/"),
    CompanyTarget("Monzo", "London", "custom", "https://monzo.com/careers"),
    CompanyTarget("Starling Bank", "London", "custom", "https://www.starlingbank.com/careers/"),
    CompanyTarget("Checkout.com", "London", "custom", "https://www.checkout.com/careers"),
    CompanyTarget("Adyen", "Amsterdam", "greenhouse", "https://careers.adyen.com/"),
    CompanyTarget("Stripe", "London", "custom", "https://stripe.com/jobs"),
    CompanyTarget("Deliveroo", "London", "custom", "https://careers.deliveroo.co.uk/"),
    CompanyTarget("Ocado Technology", "London", "custom", "https://www.ocadogroup.com/careers/"),
    CompanyTarget("Cloudflare", "London", "custom", "https://www.cloudflare.com/careers/"),
    CompanyTarget("Databricks", "London / Amsterdam", "greenhouse", "https://www.databricks.com/company/careers"),
    CompanyTarget("Snowflake", "London", "custom", "https://careers.snowflake.com/"),
    CompanyTarget("Elastic", "London / Amsterdam", "greenhouse", "https://www.elastic.co/about/careers"),
    CompanyTarget("Palantir", "London", "lever", "https://www.palantir.com/careers/"),
    CompanyTarget("Canonical", "London", "greenhouse", "https://canonical.com/careers"),
    CompanyTarget("Spotify", "London", "lever", "https://www.lifeatspotify.com/jobs"),
    CompanyTarget("Booking.com", "Amsterdam", "custom", "https://careers.booking.com/"),
    CompanyTarget("Uber", "Amsterdam", "custom", "https://www.uber.com/careers/"),
    CompanyTarget("Mollie", "Amsterdam", "custom", "https://www.mollie.com/careers"),
    CompanyTarget("Backbase", "Amsterdam", "custom", "https://www.backbase.com/company/careers"),
    CompanyTarget("Picnic", "Amsterdam", "custom", "https://jobs.picnic.app/"),
    CompanyTarget("TomTom", "Amsterdam", "custom", "https://www.tomtom.com/careers/"),
    CompanyTarget("Bunq", "Amsterdam", "custom", "https://www.bunq.com/careers"),
    CompanyTarget("WeTransfer", "Amsterdam", "custom", "https://wetransfer.com/careers"),
    CompanyTarget("Catawiki", "Amsterdam", "greenhouse", "https://www.catawiki.com/en/jobs"),
)

VERIFIED_GREENHOUSE_BOARDS = {
    "drweng": "DRW",
    "janestreet": "Jane Street",
    "jumptrading": "Jump Trading",
    "imc": "IMC Trading",
    "flowtraders": "Flow Traders",
    "wise": "Wise",
    "adyen": "Adyen",
    "databricks": "Databricks",
    "elastic": "Elastic",
    "canonical": "Canonical",
    "catawiki": "Catawiki",
}

VERIFIED_LEVER_BOARDS = {
    "palantir": "Palantir",
    "spotify": "Spotify",
}