---
name: csv-to-sif
description: Convert a CSV or Excel FF&E product list to SIF (Standard Interchange Format) for dealer and procurement systems.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
user-invocable: true
---

# /csv-to-sif — CSV to SIF Converter

Converts a CSV, Excel, or Google Sheets product list into a SIF (Standard Interchange Format) file for import into dealer and procurement systems like Hedberg, CAP, ProjectMatrix, Studio Webware, and Design Manager.

## When to Use

- Sending a specification to a dealer for quoting
- Importing product data into a dealer management system
- Sharing a standardized product list with procurement
- Converting an FF&E schedule into a format dealers expect

## SIF Format Reference

SIF is a text-based key-value format. Each product is a record starting with `PN=` (Product Number).

### Required fields
| Code | Name | Description |
|------|------|-------------|
| `PN` | Product Number | SKU or model number. Marks the start of a new record. |
| `PD` | Product Description | Product name and description |
| `MC` | Manufacturer Code | Up to 5 characters (e.g., HMI for Herman Miller, KNL for Knoll) |
| `QT` | Quantity | Integer quantity |
| `PL` | List Price | Unit list price (numeric, no currency symbol) |

### Optional fields
| Code | Name | Description |
|------|------|-------------|
| `TG` | Side Mark / Tag | Room name, area code, or project tag |
| `S-` or `S%` | Discount % | Sell price = PL - (PL × S- × 0.01) |
| `P%` or `B%` | Purchase/Buy % | Purchase cost = PL × (P% × 0.01) |
| `ON` | Option Number | Must pair with OD |
| `OD` | Option Description | Finish, fabric, color selection |
| `AN` | Attribute Number | Must pair with AD |
| `AD` | Attribute Description | Dimension, weight, or other attribute |

### File structure
```
SF=Project Name - Specification
ST=FF&E Specification - Project Name
PN=ABC-1234
PD=Eames Lounge Chair and Ottoman
MC=HMI
QT=3
PL=5695.00
TG=Executive Lounge
OD=Santos Palisander / Black MCL Leather
PN=164-500
PD=Saarinen Round Dining Table 54"
MC=KNL
QT=1
PL=4750.00
TG=Dining Area
OD=Arabescato Marble Top / White Base
```

Rules:
- Each line is one field: `CODE=VALUE`
- Lines terminated by CRLF
- `PN` starts a new record — must come first
- `ON`/`OD` and `AN`/`AD` pairs must stay together
- No embedded line breaks within a field value

## Step 1: Accept Input

**CSV file:**
```
/csv-to-sif ~/Documents/project/ffe-schedule.csv
```

**Google Sheet:**
```
/csv-to-sif 1FMScYW9guezOWc_m4ClTQxxFIpS6TNRr373R-MJGzgE
```

**Pasted CSV:**
```
/csv-to-sif
Product,Brand,SKU,Qty,Price,Finish,Room
Eames Lounge Chair,Herman Miller,670,3,5695,Walnut/Black Leather,Executive Lounge
Saarinen Table 54,Knoll,164-500,1,4750,Arabescato/White,Dining
```

## Step 2: Map Columns

Auto-detect column mappings from header names:

| CSV Column (common names) | SIF Field |
|---------------------------|-----------|
| Product Name, Name, Description, Product | PD |
| SKU, Model, Part Number, Product Number | PN |
| Brand, Manufacturer | MC (truncated to 5 chars) |
| Qty, Quantity, Count | QT |
| Price, List Price, Unit Price | PL |
| Finish, Color, Configuration | OD |
| Room, Location, Area, Tag, Side Mark | TG |
| Discount, Discount % | S- |

If using the master 33-column schema:
| Column | SIF Field |
|--------|-----------|
| C (Product Name) | PD |
| E (SKU) | PN |
| F (Brand) | MC |
| Q (Materials) | AD (with AN=MAT) |
| R (Colors/Finishes) | OD (with ON=FIN) |
| S (Selected Color/Finish) | OD (primary, replaces R if present) |
| T (List Price) | PL |
| K-O (W, D, H, Seat H, Unit) | AD (with AN=DIM, formatted as "W×D×H unit") |
| AD (Tags) | TG |

If the mapping is ambiguous, ask the user to confirm.

### Manufacturer code lookup

Convert full brand names to standard 3-5 character codes:

| Brand | MC Code |
|-------|---------|
| Herman Miller | HMI |
| Knoll | KNL |
| Steelcase | STC |
| Haworth | HAW |
| Teknion | TEK |
| Humanscale | HUM |
| Blu Dot | BLU |
| Design Within Reach | DWR |
| Fritz Hansen | FRH |
| Vitra | VIT |
| Arper | ARP |
| Muuto | MUU |
| HAY | HAY |
| Flos | FLS |
| Louis Poulsen | LPO |
| Artemide | ART |

For unknown brands, use first 3-5 characters uppercased. Flag for the user to verify.

## Step 3: Preview

Show a preview of the first 3 records before generating the file:

```
## SIF Preview (first 3 of 12 records)

Record 1:
  PN=670
  PD=Eames Lounge Chair and Ottoman
  MC=HMI
  QT=3
  PL=5695.00
  TG=Executive Lounge
  OD=Walnut / Black MCL Leather

Record 2:
  PN=164-500
  PD=Saarinen Round Dining Table 54"
  MC=KNL
  QT=1
  PL=4750.00
  TG=Dining
  OD=Arabescato Marble / White Base

...

12 records total. Generate SIF file? (y/n)
```

## Step 4: Generate SIF File

Write the `.sif` file with CRLF line endings:

```bash
# Output path
~/Documents/{project-path}/ffe-schedule.sif
# Or same directory as input CSV
{input-dir}/{input-name}.sif
```

## Step 5: Summary

```
✓ Generated ffe-schedule.sif
  12 records · 5 required fields + 2 optional per record
  Manufacturers: HMI (5), KNL (3), STC (2), BLU (2)
  Total list value: $47,830.00
  Saved to: ~/Documents/project/ffe-schedule.sif
```

## Pairs With

- `/ffe-schedule` — generate a schedule first, then convert to SIF
- `/sif-to-csv` — round-trip: CSV → SIF → send to dealer → receive updated SIF → back to CSV
- `/product-spec-bulk-cleanup` — clean up the CSV before converting
