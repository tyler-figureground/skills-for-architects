---
name: sif-to-csv
description: Convert a SIF (Standard Interchange Format) file to a clean, readable CSV or Google Sheet.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - mcp__google__sheets_values_get
  - mcp__google__sheets_values_update
  - mcp__google__sheets_spreadsheet_get
user-invocable: true
---

# /sif-to-csv — SIF to CSV Converter

Converts a SIF (Standard Interchange Format) file from a dealer or procurement system into a clean, human-readable CSV or Google Sheet. Translates field codes to column headers, expands options and attributes, and calculates totals.

## When to Use

- Received a SIF file from a dealer and need to review it as a spreadsheet
- Importing dealer pricing back into your FF&E schedule
- Comparing a dealer quote (SIF) against your original specification
- Loading dealer data into the master Google Sheet

## Step 1: Accept Input

**SIF file:**
```
/sif-to-csv ~/Documents/project/dealer-quote.sif
```

**Pasted SIF content:**
```
/sif-to-csv
SF=Project Alpha
ST=Dealer Quote - March 2026
PN=670
PD=Eames Lounge Chair and Ottoman
MC=HMI
QT=3
PL=5695.00
S-=42
TG=Executive Lounge
OD=Santos Palisander / Black MCL Leather
```

## Step 2: Parse SIF

Read the file and parse each record:

1. **Header fields**: Extract `SF` (file reference) and `ST` (specification title)
2. **Records**: Split on `PN=` boundaries — each `PN` starts a new product record
3. **For each record**, extract all fields into a structured object:
   - Required: PN, PD, MC, QT, PL
   - Optional: TG, S-/S%, P%/B%, ON/OD pairs, AN/AD pairs, PV
4. **Calculate derived values**:
   - Sell Price: `PL - (PL × S- × 0.01)` if S- is present
   - Net Price: `PL × (P% × 0.01)` if P% is present
   - Extended List: `PL × QT`
   - Extended Sell: `Sell Price × QT`

### Manufacturer code expansion

Expand common MC codes to full brand names:

| MC | Brand |
|----|-------|
| HMI | Herman Miller |
| KNL | Knoll |
| STC | Steelcase |
| HAW | Haworth |
| TEK | Teknion |
| HUM | Humanscale |
| DWR | Design Within Reach |
| FRH | Fritz Hansen |
| VIT | Vitra |
| ARP | Arper |
| FLS | Flos |
| LPO | Louis Poulsen |
| ART | Artemide |

For unknown codes, keep the code as-is and flag for the user.

### Options and attributes

- Multiple `ON`/`OD` pairs on a record → concatenate into a single "Options" column, separated by ` | `
- Multiple `AN`/`AD` pairs → concatenate into an "Attributes" column, separated by ` | `
- If AN=DIM, parse the dimension string back into W/D/H if possible

## Step 3: Present Preview

```
## SIF Import: Project Alpha — Dealer Quote March 2026

3 records parsed from dealer-quote.sif

| # | SKU | Product | Brand | Qty | List $ | Disc % | Sell $ | Ext Sell | Options | Tag |
|---|-----|---------|-------|-----|--------|--------|--------|----------|---------|-----|
| 1 | 670 | Eames Lounge Chair and Ottoman | Herman Miller | 3 | $5,695 | 42% | $3,303.10 | $9,909.30 | Santos Palisander / Black MCL | Exec Lounge |
| 2 | 164-500 | Saarinen Table 54" | Knoll | 1 | $4,750 | 38% | $2,945.00 | $2,945.00 | Arabescato / White | Dining |
| 3 | 462-CG | Gesture Chair | Steelcase | 8 | $1,189 | 45% | $653.95 | $5,231.60 | Cogent Connect / Licorice | Open Office |

**Totals:**
- List: $22,147.00
- Sell: $18,085.90
- Savings: $4,061.10 (18.3%)
```

## Step 4: Output

Ask the user for output format:

### CSV file
Save as `{input-name}-parsed.csv` with columns:

```
Item #, SKU, Product, Brand, Qty, List Price, Discount %, Sell Price, Extended List, Extended Sell, Options, Attributes, Tag, MC Code
```

### Google Sheet (master schema)
Write to the 33-column master schema:
- Column C (Product Name) ← PD
- Column E (SKU) ← PN
- Column F (Brand) ← MC expanded
- Column J (Category) ← leave for `/product-enrich`
- Column T (List Price) ← PL
- Column U (Sale Price) ← calculated sell price
- Column S (Selected Color/Finish) ← OD
- Column AD (Tags) ← TG
- Column AE (Notes) ← "From SIF: {ST}. Discount: {S-}%"
- Column AF (Status) ← "quoted"
- Column AG (Source) ← "sif-to-csv"

Quantity goes in Notes: "Qty: {QT} · Ext List: ${ext_list} · Ext Sell: ${ext_sell}"

### Markdown
Output the table in conversation.

## Step 5: Summary

```
✓ Parsed dealer-quote.sif
  Specification: Project Alpha — Dealer Quote March 2026
  3 records · 12 units
  Total list: $22,147.00
  Total sell: $18,085.90 (18.3% average discount)
  Manufacturers: HMI (1), KNL (1), STC (1)
  Saved to: ~/Documents/project/dealer-quote-parsed.csv
```

## Pairs With

- `/csv-to-sif` — round-trip: create SIF from your schedule, send to dealer, parse their quote back
- `/product-spec-bulk-cleanup` — normalize the parsed data
- `/ffe-schedule` — reformulate the dealer data into a formatted schedule
- `/product-enrich` — add categories and tags to the imported products
