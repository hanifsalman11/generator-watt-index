import os
import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://hanifsalman11.github.io/generator-watt-index").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6").strip()
CUSTOM_GEN = os.environ.get("CUSTOM_GEN", "").strip()
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "3"))

DOCS_DIR = "docs"
DATA_DIR = "data"
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_generators.json")
MONETIZATION_FILE = os.path.join(DATA_DIR, "monetization.json")

# Format: (Generator Model / Scenario, Running Watts, Peak Surge Watts, Fuel Type, Outlet Type, Fuel Gal/Hr @ 50%)
SEED_GENERATORS = [
    ("Westinghouse WGen9500DF Dual-Fuel Home Backup", 7500, 9500, "Gasoline / Propane", "NEMA L14-30R (30A 240V)", 0.68),
    ("Westinghouse WGen11500TFc Tri-Fuel w/ CO Sensor", 9500, 14500, "Gas / Propane / Nat Gas", "NEMA 14-50R (50A 240V)", 0.79),
    ("Westinghouse iGen4500DF Dual-Fuel Inverter", 3700, 4500, "Gasoline / Propane", "TT-30R (30A 120V RV)", 0.28),
    ("Honda EU7000iS Super Quiet Fuel-Injected Inverter", 5500, 7000, "Gasoline EFI", "NEMA L14-30R (30A 240V)", 0.43),
    ("Honda EU2200i Companion Parallel Inverter", 1800, 2200, "Gasoline", "NEMA 5-20R / 30A Parallel", 0.19),
    ("Duromax XP13000HXT 13,000W Tri-Fuel Beast", 10500, 13000, "Gas / Propane / Nat Gas", "NEMA 14-50R (50A 240V)", 0.88),
    ("Duromax XP9000iH 9,000W Dual-Fuel Inverter", 7600, 9000, "Gasoline / Propane", "NEMA 14-50R (50A 240V)", 0.62),
    ("Champion 201176 9,000W Tri-Fuel Open Frame Inverter", 7250, 9000, "Gas / Propane / Nat Gas", "NEMA L14-30R (30A 240V)", 0.59),
    ("Champion 100520 8,750W Dual-Fuel Inverter", 7000, 8750, "Gasoline / Propane", "NEMA L14-30R (30A 240V)", 0.56),
    ("Predator 9500 Super Quiet Inverter Generator", 7600, 9500, "Gasoline", "NEMA L14-30R (30A 240V)", 0.55),
    ("Predator 5000 Dual-Fuel Super Quiet Inverter", 3900, 5000, "Gasoline / Propane", "TT-30R (30A 120V RV)", 0.31),
    ("Generac GP8000E 8,000W Electric Start Portable", 8000, 10000, "Gasoline", "NEMA L14-30R (30A 240V)", 0.69),
    ("Generac Guardian 22kW Whole-House Standby", 19500, 22000, "Natural Gas / LP", "200A Whole-House ATS", 1.95),
    ("Generac Guardian 18kW Home Standby Generator", 17000, 18000, "Natural Gas / LP", "100A/200A Automatic ATS", 1.65),
    ("Kohler 20RCA 20kW Air-Cooled Standby Generator", 18000, 20000, "Natural Gas / LP", "200A Automatic ATS", 1.75),
    ("Firman T07571 / T07573 7,500W Tri-Fuel Portable", 7500, 9400, "Gas / Propane / Nat Gas", "NEMA L14-30R (30A 240V)", 0.67),
    ("Firman WH03242 3,200W Dual-Fuel RV Inverter", 3200, 4000, "Gasoline / Propane", "TT-30R (30A 120V RV)", 0.25),
    ("WEN DF680ix 6,800W Dual-Fuel 240V RV/Home Inverter", 5100, 6800, "Gasoline / Propane", "NEMA L14-30R (30A 240V)", 0.45),
    ("Genmax GM9000iED 9,000W Dual-Fuel Low-THD Inverter", 7200, 9000, "Gasoline / Propane", "NEMA 14-50R (50A 240V)", 0.58),
    ("Genmax GM10500iETC 10,500W Tri-Fuel Inverter", 8500, 10500, "Gas / Propane / Nat Gas", "NEMA 14-50R (50A 240V)", 0.66),
    ("Pulsar G12KBN 12,000W Dual-Fuel Home Backup", 9500, 12000, "Gasoline / Propane", "NEMA 14-50R (50A 240V)", 0.82),
    ("A-iPower GXS7100iRD 7,100W Dual-Fuel Inverter", 5700, 7100, "Gasoline / Propane", "NEMA L14-30R (30A 240V)", 0.48),
    ("Briggs & Stratton Q6500 QuietPower Series Inverter", 5000, 6500, "Gasoline", "NEMA L14-30R (30A 240V)", 0.44),
    ("DeWalt DXGNR8000 8,000W Jobsite & Home Backup", 8000, 10000, "Gasoline", "NEMA L14-30R (30A 240V)", 0.70),
    ("3-Ton Central Air Conditioner + Well Pump Backup", 7500, 9500, "Dual-Fuel / Tri-Fuel", "NEMA L14-30R (30A 240V)", 0.65),
    ("4-Ton Central AC / Heat Pump + Whole-House Backup", 9500, 12500, "Tri-Fuel 50A Setup", "NEMA 14-50R (50A 240V)", 0.80),
    ("50-Amp RV Fifth-Wheel Dual-AC Inverter Sizing", 5500, 7000, "Dual-Fuel Inverter", "NEMA 14-50R / L14-30R", 0.46),
    ("30-Amp Travel Trailer 15,000 BTU AC Inverter Sizing", 3500, 4500, "Dual-Fuel Inverter", "TT-30R (30A 120V RV)", 0.27),
    ("Submersible Deep Well Pump + Sump Pump + Fridge Backup", 5500, 7000, "240V Dual-Fuel", "NEMA L14-30R (30A 240V)", 0.45),
    ("50-Amp CS6364 / SS2-50 Power Inlet & Interlock Sizing", 9600, 12000, "Tri-Fuel 50A Setup", "NEMA 14-50R (50A 240V)", 0.78)
]


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not parse {filepath}: {e}")
    return default


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def safe_float(val, default=7500.0):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(val))
        return float(cleaned) if cleaned else float(default)
    except Exception:
        return float(default)


def build_amazon_url(search_keywords, mon_cfg):
    domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")
    encoded_q = urllib.parse.quote_plus(search_keywords)
    return f"https://{domain}/s?k={encoded_q}&tag={tag}"


def discover_google_generator_queries():
    discovered = []
    seeds = [
        "what size generator to run ",
        "westinghouse wgen ",
        "duromax tri fuel ",
        "generator transfer switch size for "
    ]
    for seed in seeds:
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q={urllib.parse.quote(seed)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for suggestion in data[1]:
                    cleaned = suggestion.lower()
                    for pref in seeds:
                        if "what size" in pref or "size for" in pref:
                            cleaned = cleaned.replace(pref, "")
                    cleaned = re.sub(
                        r"\b(calculator|size|sizing|wattage|watts|manual|review|reddit|for)\b",
                        "",
                        cleaned
                    ).strip()
                    if 5 <= len(cleaned) <= 42:
                        w_match = re.search(r"(\d{4,5})", cleaned)
                        p_w = int(w_match.group(1)) if w_match else 9500
                        r_w = int(round(p_w * 0.78, -2))
                        outlet_s = "NEMA 14-50R (50A 240V)" if r_w >= 8500 else "NEMA L14-30R (30A 240V)"
                        discovered.append((cleaned.title(), r_w, p_w, "Gasoline / Propane", outlet_s, 0.65))
        except Exception as e:
            print(f"[WARN] Google Suggest notice: {e}")
    return discovered


def build_deterministic_generator_data(gen_tuple):
    """Mesin Fisika Daya Kejut LRA, NEC Article 702 Transfer Switch & Konsumsi BBM (100% bebas gagal)."""
    gen_name, run_w, peak_w, fuel_type, outlet_type, gal_hr_50 = gen_tuple

    # Penurunan daya (Derating) bahan bakar: Propane = 90% dari Bensin, Natural Gas = 80% dari Bensin
    lp_run_w = int(round(run_w * 0.90, -1))
    ng_run_w = int(round(run_w * 0.80, -1))

    # Spesifikasi Transfer Switch, Inlet Box & Kabel Tembaga (NEC 702)
    if run_w >= 8500:
        amp_service = 50
        inlet_plug = "50A CS6364 / NEMA SS2-50P Twist-Lock Inlet"
        cord_awg = "6/3 + 8/1 AWG (50-Amp Heavy-Duty STW Pure Copper Cord)"
        max_cont_watts = 12000
    elif run_w >= 4500:
        amp_service = 30
        inlet_plug = "30A NEMA L14-30P 4-Prong Twist-Lock Inlet"
        cord_awg = "10/4 AWG (30-Amp SJTW/STW Pure Copper Cord)"
        max_cont_watts = 7200
    else:
        amp_service = 30
        inlet_plug = "30A NEMA TT-30P (120V RV / Household Transfer)"
        cord_awg = "10/3 AWG (30-Amp 120V Heavy-Duty Cord)"
        max_cont_watts = 3600

    # Konsumsi Propane (1 Galon LP = 4.24 lbs; mesin genset membakar ~1.22x volume galon LP dibanding bensin)
    lp_gal_hr = round(gal_hr_50 * 1.22, 2)
    tank_20lb_hrs = round(4.7 / max(0.2, lp_gal_hr), 1)

    return {
        "generator_name": gen_name,
        "fuel_type": fuel_type,
        "seo_title": f"{gen_name} Wattage, Transfer Switch & Fuel Burn Calculator (2026)",
        "meta_description": f"Calculate exact running watts ({run_w:,}W gas / {lp_run_w:,}W propane), AC starting surge LRA, {amp_service}A transfer switch wire size ({cord_awg}), and fuel runtime for {gen_name}.",
        "specs": {
            "running_watts_gas": run_w,
            "peak_surge_watts": peak_w,
            "running_watts_propane": lp_run_w,
            "running_watts_natgas": ng_run_w,
            "fuel_type": fuel_type,
            "primary_outlet": outlet_type,
            "transfer_switch_amps": amp_service,
            "recommended_inlet_box": inlet_plug,
            "recommended_cord_awg": cord_awg,
            "gal_per_hr_50pct": gal_hr_50,
            "propane_20lb_runtime_hrs": tank_20lb_hrs
        },
        "electrical_verdict": f"Rated at {run_w:,} Running Watts and {peak_w:,} Peak Starting Watts on gasoline ({lp_run_w:,}W on Liquid Propane / {ng_run_w:,}W on Natural Gas), the {gen_name} connects to your home panel via a {amp_service}-Amp ({outlet_type}) circuit using {cord_awg}. At 50% household load, it burns ~{gal_hr_50} gal/hr of gasoline or ~{lp_gal_hr} gal/hr of propane (running ~{tank_20lb_hrs} hours on a standard 20-lb BBQ propane cylinder).",
        "hardware_bundle": [
            {
                "badge": f"{peak_w:,}W Backup Generator",
                "title": f"{gen_name} ({run_w:,}W Running / {peak_w:,}W Peak)",
                "price_range": "$599 - $2,499",
                "amazon_query": f"{gen_name} Generator",
                "gen_note": f"Delivers {run_w:,}W continuous output via {outlet_type} with electric start and low-oil shutdown."
            },
            {
                "badge": f"{amp_service}A Transfer & Inlet Kit",
                "title": f"{amp_service}-Amp Pre-Wired Manual Transfer Switch + Weatherproof {inlet_plug} Box",
                "price_range": "$99 - $389",
                "amazon_query": f"{amp_service} Amp Generator Transfer Switch Power Inlet Box Kit UL Listed",
                "gen_note": f"NEC Article 702 compliant isolation prevents lethal utility backfeeding and handles up to {max_cont_watts:,}W."
            },
            {
                "badge": f"{amp_service}A Pure Copper Cord",
                "title": f"25ft / 50ft {cord_awg} Twist-Lock Generator Extension Cord (UL Listed)",
                "price_range": "$79 - $229",
                "amazon_query": f"50ft {amp_service} Amp Generator Cord {cord_awg.split()[0]} AWG Twist Lock",
                "gen_note": "Positions the generator 25+ feet away from windows to prevent carbon monoxide (CO) intrusion."
            },
            {
                "badge": "A/C Compressor Soft Starter",
                "title": "Residential Central A/C & Heat Pump Soft Starter (Cuts Startup LRA Surge by 65%–70%)",
                "price_range": "$169 - $349",
                "amazon_query": "Air Conditioner Soft Starter Home AC Generator 3 Ton 4 Ton",
                "gen_note": f"Drops a 3-to-4 Ton central AC startup surge from 11,000W down to ~3,600W so a {run_w:,}W generator starts it effortlessly."
            }
        ],
        "outage_checklist": [
            f"Account for Fuel Derating when sizing appliances: switching from Gasoline ({run_w:,}W) to Propane drops continuous output by ~10% ({lp_run_w:,}W), and Natural Gas drops output by ~20% ({ng_run_w:,}W).",
            "Install a Central A/C Soft Starter on your outdoor condenser unit; without one, a 3-Ton AC compressor draws 75–95 Locked Rotor Amps (18,000W+ instantaneous surge) and trips your generator breaker.",
            f"Unbond the generator's Neutral-to-Frame jumper ONLY if connecting to a standard Panel Interlock Kit or 2-pole Transfer Switch where Neutral is already bonded inside your main house panel (NEC 250.20).",
            "Always stagger high-inrush motor loads during an outage: start your 240V deep well pump and refrigerator first, wait 30 seconds, and then engage your central air conditioner or heat pump."
        ],
        "faqs": [
            {
                "q": f"Can the {gen_name} run a 3-Ton or 4-Ton central air conditioner?",
                "a": f"A 3-Ton central AC uses ~3,200 running watts but demands 8,500W–11,000W of starting surge (LRA). With {peak_w:,} peak watts ({run_w:,}W running), installing a Soft Starter on the AC condenser drops startup surge to ~3,600W, allowing the {gen_name} to run your central AC, well pump, and refrigerators simultaneously."
            },
            {
                "q": f"How much fuel does the {gen_name} burn per hour and per day?",
                "a": f"At a typical 50% household load, it consumes ~{gal_hr_50} gallons/hour of gasoline (~{round(gal_hr_50 * 24, 1)} gallons per 24 hours) or ~{lp_gal_hr} gallons/hour of liquid propane (lasting ~{tank_20lb_hrs} hours on a 20-lb tank or ~{round(tank_20lb_hrs * 5, 1)} hours on a 100-lb propane tank)."
            },
            {
                "q": f"Do I need a 30-Amp or 50-Amp inlet box and cord for the {gen_name}?",
                "a": f"A 30-Amp NEMA L14-30 circuit maxes out at 7,200 Watts (30A × 240V), whereas a 50-Amp CS6364/SS2-50 circuit handles up to 12,000 Watts (50A × 240V). For the {gen_name}, use a {amp_service}-Amp inlet box wired with {cord_awg}."
            }
        ]
    }


def generate_gen_data(gen_tuple):
    if not GEMINI_API_KEY:
        return build_deterministic_generator_data(gen_tuple)

    gen_name, run_w, peak_w, fuel_type, outlet_type, gal_hr_50 = gen_tuple
    lp_run_w = int(round(run_w * 0.90, -1))
    ng_run_w = int(round(run_w * 0.80, -1))
    amp_service = 50 if run_w >= 8500 else 30
    inlet_plug = "50A CS6364 / SS2-50P Inlet" if amp_service == 50 else "30A NEMA L14-30P Inlet"
    cord_awg = "6/3+8/1 AWG Copper Cord" if amp_service == 50 else "10/4 AWG Copper Cord"
    tank_20_hrs = round(4.7 / max(0.2, gal_hr_50 * 1.22), 1)

    prompt = f"""
You are a Master Licensed Electrician (NEC Article 702 Standby Systems Specialist) & Backup Power Engineer. Create an accurate 2026 running vs starting surge wattage, 30A/50A transfer switch, and fuel consumption guide for: "{gen_name}".
Baseline specs: Running Watts={run_w}W Gas ({lp_run_w}W LP / {ng_run_w}W NG), Peak Surge={peak_w}W, Fuel={fuel_type}, Outlet={outlet_type}, Transfer Switch={amp_service}A ({inlet_plug}, {cord_awg}), Fuel Burn @ 50%={gal_hr_50} gal/hr ({tank_20_hrs} hrs on 20lb LP).
Return ONLY a valid JSON object matching this exact schema:
{{
  "generator_name": "{gen_name}",
  "fuel_type": "{fuel_type}",
  "seo_title": "{gen_name} Wattage, Transfer Switch & Fuel Burn Calculator (2026)",
  "meta_description": "Calculate exact running vs starting surge watts, 30A/50A transfer switch wire gauge, and gas/propane consumption for {gen_name}.",
  "specs": {{
    "running_watts_gas": {run_w},
    "peak_surge_watts": {peak_w},
    "running_watts_propane": {lp_run_w},
    "running_watts_natgas": {ng_run_w},
    "fuel_type": "{fuel_type}",
    "primary_outlet": "{outlet_type}",
    "transfer_switch_amps": {amp_service},
    "recommended_inlet_box": "{inlet_plug}",
    "recommended_cord_awg": "{cord_awg}",
    "gal_per_hr_50pct": {gal_hr_50},
    "propane_20lb_runtime_hrs": {tank_20_hrs}
  }},
  "electrical_verdict": "3-sentence technical summary stating gas/propane/NG running watts, peak surge watts, required 30A/50A inlet & cord AWG, and fuel consumption per hour.",
  "hardware_bundle": [
    {{
      "badge": "Backup Generator",
      "title": "{gen_name}",
      "price_range": "$599 - $2,499",
      "amazon_query": "{gen_name} Generator",
      "gen_note": "1-sentence wattage and outlet note"
    }},
    {{
      "badge": "{amp_service}A Transfer & Inlet",
      "title": "{amp_service}-Amp Manual Transfer Switch + Weatherproof {inlet_plug} Box",
      "price_range": "$99 - $389",
      "amazon_query": "{amp_service} Amp Generator Transfer Switch Power Inlet Box",
      "gen_note": "1-sentence NEC 702 backfeed safety note"
    }},
    {{
      "badge": "{amp_service}A Pure Copper Cord",
      "title": "50ft {amp_service}-Amp Heavy-Duty Twist-Lock Generator Cord ({cord_awg})",
      "price_range": "$79 - $229",
      "amazon_query": "50ft {amp_service} Amp Generator Extension Cord Twist Lock",
      "gen_note": "1-sentence carbon monoxide distance and voltage drop note"
    }},
    {{
      "badge": "Central A/C Soft Starter",
      "title": "Residential Central Air Conditioner Soft Starter (65% LRA Surge Reduction)",
      "price_range": "$169 - $349",
      "amazon_query": "Air Conditioner Soft Starter Generator 3 Ton 4 Ton",
      "gen_note": "1-sentence compressor locked-rotor amp reduction note"
    }}
  ],
  "outage_checklist": [
    "Step 1 regarding 10% propane and 20% natural gas wattage derating",
    "Step 2 regarding A/C compressor soft starter for LRA surge reduction",
    "Step 3 regarding floating vs bonded neutral for panel interlocks",
    "Step 4 regarding staggering 240V well pump and HVAC startup loads"
  ],
  "faqs": [
    {{"q": "Can the {gen_name} run a central air conditioner and well pump?", "a": "Exact running vs LRA surge watts with and without a soft starter."}},
    {{"q": "How much gas or propane does the {gen_name} use per hour?", "a": "Exact gal/hr and 20lb/100lb propane tank runtime hours."}},
    {{"q": "Do I need a 30A or 50A transfer switch for the {gen_name}?", "a": "Exact 7,200W (30A) vs 12,000W (50A) NEC comparison."}}
  ]
}}
"""

    for model_id in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)
                if "specs" in parsed and "hardware_bundle" in parsed:
                    return parsed
        except Exception as e:
            print(f"[WARN] Gemini ({model_id}) notice for '{gen_name}': {e}")

    return build_deterministic_generator_data(gen_tuple)


def build_generator_html_page(data, slug, mon_cfg):
    gen_name = data.get("generator_name", "Home Backup Generator")
    sp = data.get("specs", {})
    run_w = int(safe_float(sp.get("running_watts_gas", 7500), 7500))
    peak_w = int(safe_float(sp.get("peak_surge_watts", 9500), 9500))
    lp_w = int(safe_float(sp.get("running_watts_propane", int(run_w * 0.9)), 6750))
    ng_w = int(safe_float(sp.get("running_watts_natgas", int(run_w * 0.8)), 6000))
    outlet_s = sp.get("primary_outlet", "NEMA L14-30R (30A 240V)")
    ts_amps = int(safe_float(sp.get("transfer_switch_amps", 30), 30))
    cord_awg = sp.get("recommended_cord_awg", "10/4 AWG Pure Copper")
    gal_hr = round(safe_float(sp.get("gal_per_hr_50pct", 0.65), 0.65), 2)
    lp_20_hrs = round(safe_float(sp.get("propane_20lb_runtime_hrs", 5.9), 5.9), 1)

    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Tri+Fuel+Home+Backup+Generator+Transfer+Switch"), mon_cfg)

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": f"{gen_name} Wattage, LRA Surge & Fuel Calculator",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web Browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
                    } for f in data.get("faqs", [])
                ]
            }
        ]
    }

    bundle_html = ""
    for item in data.get("hardware_bundle", []):
        amz_url = build_amazon_url(item.get("amazon_query", item.get("title", "Tri Fuel Backup Generator")), mon_cfg)
        bundle_html += f"""
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col justify-between hover:border-amber-500/60 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded">{item.get('badge', 'Backup Gear')}</span>
              <span class="text-sm font-bold text-emerald-400">{item.get('price_range', '$99+')}</span>
            </div>
            <h3 class="text-base font-bold text-white mt-2">{item.get('title', '')}</h3>
            <p class="text-xs text-zinc-400 mt-2 leading-relaxed">⚡ {item.get('gen_note', '')}</p>
          </div>
          <a href="{amz_url}" target="_blank" rel="nofollow sponsored" class="mt-5 block text-center bg-amber-500 hover:bg-amber-400 text-zinc-950 font-extrabold py-2.5 px-4 rounded-lg text-sm transition shadow-lg">
            Check Price on Amazon →
          </a>
        </div>"""

    # Build Appliance Running vs Starting Surge Wattage Reference Matrix
    app_tiers = [
        ("3-Ton Central A/C (Factory LRA)", "3,200W Running", "9,500W Surge", "Needs 11,000W+ Gen"),
        ("3-Ton Central A/C (w/ Soft Starter)", "3,200W Running", "3,800W Surge (-60%)", "Runs on 6,500W+ Gen"),
        ("3/4 HP 240V Submersible Well Pump", "1,500W Running", "4,200W Surge", "Runs on 5,500W+ Gen"),
        ("1/2 HP Basement Sump Pump", "1,050W Running", "2,400W Surge", "Runs on 3,500W+ Gen"),
        ("Energy-Star Refrigerator + Freezer", "700W Running", "2,100W Surge", "Runs on 2,200W+ Inverter"),
        ("50-Gal Electric Water Heater (240V)", "4,500W Running", "4,500W Resistive", "Needs 30A/50A Load Shed")
    ]
    matrix_rows_html = ""
    for a_name, r_str, s_str, v_str in app_tiers:
        matrix_rows_html += f"""
        <tr class="border-b border-zinc-800 hover:bg-zinc-800/40">
          <td class="py-3 px-4 font-bold text-white">{a_name}</td>
          <td class="py-3 px-4 text-zinc-300">{r_str}</td>
          <td class="py-3 px-4 font-bold text-amber-400">{s_str}</td>
          <td class="py-3 px-4 text-xs text-emerald-400 font-semibold">{v_str}</td>
        </tr>"""

    checklist_html = ""
    for idx, step_text in enumerate(data.get("outage_checklist", []), start=1):
        checklist_html += f"""
        <label class="flex items-start gap-3.5 bg-zinc-900 border border-zinc-800 rounded-xl p-4 cursor-pointer hover:border-zinc-700 transition">
          <input type="checkbox" class="mt-1 w-5 h-5 accent-amber-500 rounded cursor-pointer gen-check">
          <span class="text-sm text-zinc-200 leading-relaxed"><strong>NEC 702 Step {idx}:</strong> {step_text}</span>
        </label>"""

    faqs_html = "".join([
        f"<div class='bg-zinc-900 border border-zinc-800 rounded-xl p-5'><h3 class='font-bold text-white text-base mb-2'>{f.get('q', '')}</h3><p class='text-sm text-zinc-300 leading-relaxed'>{f.get('a', '')}</p></div>"
        for f in data.get("faqs", [])
    ])

    canonical_url = f"{SITE_BASE_URL}/{slug}.html"
    amz_domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    amz_tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data.get('seo_title', gen_name)}</title>
  <meta name="description" content="{data.get('meta_description', '')}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{data.get('seo_title', gen_name)}">
  <meta property="og:description" content="{data.get('meta_description', '')}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{json.dumps(schema_graph)}</script>
</head>
<body class="bg-zinc-950 text-zinc-100 antialiased min-h-screen flex flex-col">
  <header class="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur sticky top-0 z-30">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <a href="index.html" class="text-lg font-black tracking-tight text-white flex items-center gap-2">
        <span class="bg-amber-500 text-zinc-950 px-2 py-0.5 rounded font-black">WATT</span>GenIndex
      </a>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-amber-500 hover:bg-amber-400 text-zinc-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Generators & Transfer Switches →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-10 flex-1 w-full">
    <div class="mb-8">
      <div class="flex flex-wrap items-center gap-2.5 mb-3">
        <span class="text-xs font-extrabold uppercase tracking-widest bg-amber-500 text-zinc-950 px-3 py-1 rounded-full">{run_w:,}W Run / {peak_w:,}W Peak</span>
        <span class="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">LP: {lp_w:,}W | NG: {ng_w:,}W</span>
        <span class="text-xs font-semibold bg-zinc-800 text-zinc-300 px-3 py-1 rounded-full">{outlet_s} | {ts_amps}A Switch</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white leading-tight">{data.get('seo_title', gen_name)}</h1>
      <div class="mt-4 bg-zinc-900 border-l-4 border-amber-500 p-4 rounded-r-xl text-sm text-zinc-200 leading-relaxed">
        <strong>NEC Article 702 & LRA Surge Verdict:</strong> {data.get('electrical_verdict', '')}
      </div>
    </div>

    <!-- INTERACTIVE SURGE WATTAGE (LRA), SOFT-STARTER & FUEL BURN CALCULATOR -->
    <section class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 sm:p-8 mb-12 shadow-2xl">
      <h2 class="text-xl font-extrabold text-white mb-2">Interactive {gen_name} Load, Soft-Starter & Fuel Calculator</h2>
      <p class="text-xs text-zinc-400 mb-6">Select your home appliances, central A/C soft-starter status, and fuel type to compute total running watts, peak starting surge (LRA), required 30A/50A transfer switch, and 24-hour fuel consumption.</p>

      <div class="grid md:grid-cols-2 gap-8 items-center">
        <div class="space-y-5">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="acSelect" class="block text-xs font-medium text-zinc-400 mb-1">Central A/C or Heat Pump</label>
              <select id="acSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500">
                <option value="0|0">No A/C (Heating Blower Only)</option>
                <option value="2200|6500">2-Ton Central A/C (2,200W)</option>
                <option value="3200|9500" selected>3-Ton Central A/C (3,200W)</option>
                <option value="4200|12500">4-Ton Central A/C (4,200W)</option>
              </select>
            </div>
            <div>
              <label for="softSelect" class="block text-xs font-medium text-zinc-400 mb-1">A/C Compressor Soft Starter</label>
              <select id="softSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500">
                <option value="0.38" selected>Installed (-62% LRA Surge)</option>
                <option value="1.00">Not Installed (Factory LRA)</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="wellSelect" class="block text-xs font-medium text-zinc-400 mb-1">Well Pump / Sump Pump</label>
              <select id="wellSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500">
                <option value="0|0">City Water (No Well Pump)</option>
                <option value="1050|2200">1/2 HP Sump Pump (1,050W)</option>
                <option value="1500|4000" selected>3/4 HP 240V Well Pump (1,500W)</option>
                <option value="2000|5500">1.0 HP Deep Well Pump (2,000W)</option>
              </select>
            </div>
            <div>
              <label for="fuelSelect" class="block text-xs font-medium text-zinc-400 mb-1">Selected Generator Fuel</label>
              <select id="fuelSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500">
                <option value="1.00|gas">Gasoline (100% Rated Output)</option>
                <option value="0.90|lp" selected>Liquid Propane (-10% Derate)</option>
                <option value="0.80|ng">Natural Gas (-20% Derate)</option>
              </select>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="baseSlider" class="text-zinc-300">Fridge, Freezer, Lights, Wi-Fi & TVs (Running Watts)</label>
              <span class="text-amber-400 font-bold"><span id="baseVal">1,400</span> W</span>
            </div>
            <input id="baseSlider" type="range" min="500" max="5000" step="100" value="1400" class="w-full accent-amber-500 cursor-pointer">
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-zinc-950 border border-amber-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-amber-400 font-bold">Total Load & Peak LRA</span>
            <div class="text-xl sm:text-2xl font-black text-white mt-1"><span id="runLoadOut">6,100</span>W <span class="text-xs font-normal text-zinc-400">Run</span></div>
            <p id="surgeLoadOut" class="text-xs text-amber-400 font-semibold mt-1">Peak Surge: 8,510W</p>
          </div>

          <div class="bg-zinc-950 border border-emerald-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-emerald-400 font-bold">Switch & Fuel Burn</span>
            <div id="switchSpecOut" class="text-xl sm:text-2xl font-black text-emerald-400 mt-1">30A / 50A Kit</div>
            <p id="fuelBurnOut" class="text-xs text-zinc-300 font-semibold mt-1">~0.75 Gal/hr (18 Gal/day)</p>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-amber-950/40 border border-amber-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div id="genAdviceBanner" class="text-sm text-amber-100 font-medium"></div>
        <a id="dynamicGenBtn" href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="shrink-0 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-extrabold px-4 py-2.5 rounded-lg text-xs uppercase tracking-wider transition">
          Shop Matched Generator & Switch on Amazon →
        </a>
      </div>
    </section>

    <!-- 4-CARD HARDWARE BUNDLE -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Complete {gen_name} Transfer Switch, Cord & Soft-Starter Kit</h2>
        <span class="text-xs text-zinc-400">UL-1008 & NEC Article 702 Compliant</span>
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{bundle_html}</div>
    </section>

    <!-- APPLIANCE SURGE MATRIX TABLE -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-4">Household 240V/120V Appliance Running vs. Starting Surge (LRA) Chart</h2>
      <div class="overflow-x-auto bg-zinc-900 border border-zinc-800 rounded-xl">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-zinc-800 bg-zinc-950/60 text-zinc-400 uppercase text-xs">
              <th class="py-3.5 px-4">Household Motor / Appliance</th>
              <th class="py-3.5 px-4">Continuous Running Watts</th>
              <th class="py-3.5 px-4 text-amber-400">Starting Surge Watts (LRA)</th>
              <th class="py-3.5 px-4 text-emerald-400">Generator Sizing Verdict</th>
            </tr>
          </thead>
          <tbody>{matrix_rows_html}</tbody>
        </table>
      </div>
    </section>

    <!-- NEC 702 CHECKLIST -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Master Electrician NEC 702 Backup Power & Neutral Bonding Checklist</h2>
        <span id="genBadge" class="text-xs font-bold bg-zinc-800 text-amber-400 px-3 py-1 rounded-full">0 / 4 Completed</span>
      </div>
      <div class="space-y-3">{checklist_html}</div>
    </section>

    <!-- FAQ -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-5">Frequently Asked Questions ({gen_name})</h2>
      <div class="space-y-4">{faqs_html}</div>
    </section>
  </main>

  <footer class="border-t border-zinc-800 py-8 text-center text-xs text-zinc-500 px-4">
    <p>© {datetime.now(timezone.utc).year} WattGenIndex. Independent Backup Generator & NEC 702 Sizing Database. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const baseGenRunW = {run_w};
    const baseGenPeakW = {peak_w};
    const amzDomain = "{amz_domain}";
    const amzTag = "{amz_tag}";

    const acSelect = document.getElementById('acSelect');
    const softSelect = document.getElementById('softSelect');
    const wellSelect = document.getElementById('wellSelect');
    const fuelSelect = document.getElementById('fuelSelect');
    const baseSlider = document.getElementById('baseSlider');
    const baseVal = document.getElementById('baseVal');
    const runLoadOut = document.getElementById('runLoadOut');
    const surgeLoadOut = document.getElementById('surgeLoadOut');
    const switchSpecOut = document.getElementById('switchSpecOut');
    const fuelBurnOut = document.getElementById('fuelBurnOut');
    const genAdviceBanner = document.getElementById('genAdviceBanner');
    const dynamicGenBtn = document.getElementById('dynamicGenBtn');

    function recalculateGen() {{
      const acParts = acSelect.value.split('|');
      const acRun = parseInt(acParts[0], 10);
      const acRawSurge = parseInt(acParts[1], 10);
      const softMult = parseFloat(softSelect.value);

      const wellParts = wellSelect.value.split('|');
      const wellRun = parseInt(wellParts[0], 10);
      const wellSurge = parseInt(wellParts[1], 10);

      const fuelParts = fuelSelect.value.split('|');
      const fuelDerate = parseFloat(fuelParts[0]);
      const fuelCode = fuelParts[1];

      const baseRun = parseInt(baseSlider.value, 10);
      baseVal.textContent = baseRun.toLocaleString();

      const acEffSurge = Math.round(acRawSurge * softMult);
      const totalRunW = acRun + wellRun + baseRun;
      const highestMotorExtraSurge = Math.max(
        Math.max(0, acEffSurge - acRun),
        Math.max(0, wellSurge - wellRun),
        800
      );
      const totalPeakSurgeW = totalRunW + highestMotorExtraSurge;

      const reqGasRunWatts = Math.ceil((totalRunW / fuelDerate) * 1.15 / 500) * 500;
      const reqGasPeakWatts = Math.ceil((totalPeakSurgeW / fuelDerate) / 500) * 500;
      const finalRecGenWatts = Math.max(reqGasRunWatts, reqGasPeakWatts);

      const need50A = totalRunW > 6800;
      const switchLabel = need50A ? "50A (6 AWG Cord)" : "30A (10 AWG Cord)";
      const inletCode = need50A ? "50+Amp+SS2-50" : "30+Amp+L14-30";

      const estGalHrGas = (totalRunW / 1000.0) * 0.115;
      let fuelText = `${{estGalHrGas.toFixed(2)}} Gal/hr Gas (${{(estGalHrGas * 24).toFixed(1)}} Gal/d)`;
      if (fuelCode === 'lp') {{
        const lpGalHr = estGalHrGas * 1.22;
        fuelText = `${{lpGalHr.toFixed(2)}} Gal/hr LP (~${{(4.7 / Math.max(0.2, lpGalHr)).toFixed(1)}}h / 20lb Tank)`;
      }} else if (fuelCode === 'ng') {{
        const ngCfh = Math.round((totalRunW / 1000.0) * 14.5);
        fuelText = `~${{ngCfh}} CFH (${{(ngCfh * 1000).toLocaleString()}} BTU/hr NG)`;
      }}

      runLoadOut.textContent = totalRunW.toLocaleString();
      surgeLoadOut.textContent = `Peak LRA Surge: ${{totalPeakSurgeW.toLocaleString()}}W`;
      switchSpecOut.textContent = switchLabel;
      fuelBurnOut.textContent = fuelText;

      genAdviceBanner.innerHTML = `⚡ <strong>NEC 702 Sizing Spec:</strong> Your appliances draw <strong>${{totalRunW.toLocaleString()}}W running</strong> and <strong>${{totalPeakSurgeW.toLocaleString()}}W starting surge</strong>. Pair a <strong>${{finalRecGenWatts.toLocaleString()}}W Dual/Tri-Fuel Generator</strong> with a <strong>${{switchLabel}} Transfer Switch</strong>.`;
      dynamicGenBtn.href = `https://${{amzDomain}}/s?k=${{finalRecGenWatts}}W+Tri+Fuel+Dual+Fuel+Generator+${{inletCode}}+Transfer+Switch&tag=${{amzTag}}`;
    }}

    acSelect.addEventListener('change', recalculateGen);
    softSelect.addEventListener('change', recalculateGen);
    wellSelect.addEventListener('change', recalculateGen);
    fuelSelect.addEventListener('change', recalculateGen);
    baseSlider.addEventListener('input', recalculateGen);
    recalculateGen();

    const checks = document.querySelectorAll('.gen-check');
    const badge = document.getElementById('genBadge');
    checks.forEach(ch => {{
      ch.addEventListener('change', () => {{
        const done = Array.from(checks).filter(c => c.checked).length;
        badge.textContent = `${{done}} / ${{checks.length}} Completed`;
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)


def rebuild_portal_sitemap_and_rss(published, mon_cfg):
    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Tri+Fuel+Home+Backup+Generator+Transfer+Switch"), mon_cfg)

    cards_html = ""
    for item in reversed(published):
        cards_html += f"""
        <a href="{item['slug']}.html" class="block bg-zinc-900 border border-zinc-800 hover:border-amber-500/60 rounded-xl p-5 transition group">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-black uppercase bg-amber-500 text-zinc-950 px-2.5 py-0.5 rounded">{item.get('run_w', 7500):,}W Run / {item.get('peak_w', 9500):,}W Peak</span>
            <span class="text-xs text-zinc-400">{item.get('ts_amps', 30)}A Transfer</span>
          </div>
          <h2 class="text-base font-bold text-white group-hover:text-amber-400 transition">{item['generator_name']}</h2>
          <p class="text-xs text-zinc-400 mt-2 line-clamp-2">{item['description']}</p>
          <span class="inline-block mt-4 text-xs font-extrabold text-amber-400">Calculate Surge Watts & Fuel Burn →</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WattGenIndex — Home Backup Generator Wattage, 30A/50A Transfer Switch & Fuel Calculator (2026)</title>
  <meta name="description" content="Calculate exact home backup generator running watts, central A/C starting surge (LRA), 30A/50A transfer switch wire gauge, and propane/gasoline consumption for Westinghouse, Honda, Duromax, Generac, and Champion generators.">
  <link rel="canonical" href="{SITE_BASE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="WattGenIndex RSS Feed" href="{SITE_BASE_URL}/rss.xml">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col">
  <header class="border-b border-zinc-800 bg-zinc-900/80 sticky top-0 z-30 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <div class="text-lg font-black text-white flex items-center gap-2">
        <span class="bg-amber-500 text-zinc-950 px-2 py-0.5 rounded font-black">WATT</span>GenIndex
      </div>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-amber-500 hover:bg-amber-400 text-zinc-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Generators & Transfer Switches →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-12 flex-1 w-full">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <h1 class="text-3xl sm:text-5xl font-black text-white tracking-tight">Home Backup Generator Wattage, Transfer Switch & Fuel Database</h1>
      <p class="text-zinc-400 mt-3 text-base sm:text-lg">Select your generator model or household backup scenario below to calculate central A/C starting surge (LRA), 30A/50A inlet cord gauge, and 24-hour gas/propane consumption.</p>
      <div class="mt-6">
        <input id="filterInput" type="text" placeholder="Search generator or scenario (e.g. Westinghouse WGen9500DF, Honda EU7000iS, Duromax, 3-Ton AC, 50 Amp...)" class="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-amber-500">
      </div>
    </div>

    <div id="genGrid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards_html}</div>
  </main>

  <footer class="border-t border-zinc-800 py-8 text-center text-xs text-zinc-500">
    <p>© {datetime.now(timezone.utc).year} WattGenIndex. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    const cards = Array.from(document.getElementById('genGrid').children);
    filterInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.textContent.toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in published:
        urls_xml += f"""  <url>
    <loc>{SITE_BASE_URL}/{item['slug']}.html</loc>
    <lastmod>{item.get('date', today)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>""")

    rss_items = ""
    for item in list(reversed(published))[:30]:
        rss_items += f"""    <item>
      <title>{item['title']}</title>
      <link>{SITE_BASE_URL}/{item['slug']}.html</link>
      <guid>{SITE_BASE_URL}/{item['slug']}.html</guid>
      <description>{item['description']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>WattGenIndex Backup Generator & Transfer Switch Sizing Database</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Interactive Home Backup Generator Wattage, LRA Surge & Fuel Consumption Calculators</description>
    <atom:link href="{SITE_BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
{rss_items}  </channel>
</rss>"""

    with open(os.path.join(DOCS_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def notify_search_engines(new_urls):
    if not SITE_BASE_URL or not new_urls:
        return
    parsed_host = urllib.parse.urlparse(SITE_BASE_URL).netloc
    payload = {
        "host": parsed_host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls
    }
    try:
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[INDEXNOW] Pushed {len(new_urls)} URLs (HTTP {resp.status})")
    except Exception as e:
        print(f"[WARN] IndexNow ping notice: {e}")

    try:
        hub_data = urllib.parse.urlencode({
            "hub.mode": "publish",
            "hub.url": f"{SITE_BASE_URL}/rss.xml"
        }).encode("utf-8")
        req_hub = urllib.request.Request(
            "https://pubsubhubbub.appspot.com/",
            data=hub_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req_hub, timeout=15) as resp_hub:
            print(f"[WEBSUB] Google PubSubHubbub ping status: {resp_hub.status}")
    except Exception as e:
        print(f"[WARN] WebSub ping notice: {e}")


def main():
    published = load_json(PUBLISHED_FILE, [])
    mon_cfg = load_json(MONETIZATION_FILE, {})
    published_slugs = {item["slug"] for item in published}

    candidates = []
    if CUSTOM_GEN:
        candidates.append((CUSTOM_GEN.strip(), 7500, 9500, "Gasoline / Propane", "NEMA L14-30R (30A 240V)", 0.65))
    candidates.extend(SEED_GENERATORS)
    candidates.extend(discover_google_generator_queries())

    new_urls = []
    count = 0

    for gen_tuple in candidates:
        if count >= PAGES_PER_RUN:
            break
        g_name = gen_tuple[0]
        slug = slugify(f"{g_name}-wattage-transfer-switch-calculator")
        if slug in published_slugs:
            continue

        print(f"[ENGINE] Generating backup generator wattage & transfer switch calculator for: {g_name}...")
        try:
            data = generate_gen_data(gen_tuple)
            build_generator_html_page(data, slug, mon_cfg)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sp = data.get("specs", {})

            published.append({
                "generator_name": data.get("generator_name", g_name),
                "slug": slug,
                "title": data.get("seo_title", f"{g_name} Wattage Calculator"),
                "description": data.get("meta_description", ""),
                "run_w": int(safe_float(sp.get("running_watts_gas", gen_tuple[1]), gen_tuple[1])),
                "peak_w": int(safe_float(sp.get("peak_surge_watts", gen_tuple[2]), gen_tuple[2])),
                "ts_amps": int(safe_float(sp.get("transfer_switch_amps", 30), 30)),
                "date": today
            })
            published_slugs.add(slug)
            if SITE_BASE_URL:
                new_urls.append(f"{SITE_BASE_URL}/{slug}.html")
            count += 1
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Failed building {g_name}: {e}")

    save_json(PUBLISHED_FILE, published)
    rebuild_portal_sitemap_and_rss(published, mon_cfg)
    if new_urls and SITE_BASE_URL:
        new_urls.append(f"{SITE_BASE_URL}/")
        notify_search_engines(new_urls)
    print(f"[DONE] Published {count} new generator wattage & transfer switch calculator pages.")


if __name__ == "__main__":
    main()
