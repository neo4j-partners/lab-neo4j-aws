# Data Quality Issues

Issues identified by comparing the Neo4j database (`neo4j+s://9a562687.databases.neo4j.io`) against the exported seed data in `setup/seed-data/`. These originate from the KGBuilder/SimpleKGPipeline LLM extraction, not from the seed export process itself.

## Critical

### 1. COMPETES_WITH relationships are severely polluted

The KGBuilder pipeline consistently misclassifies subsidiaries, acquisitions, suppliers, and partners as competitors.

**PG&E (PCG):** 12 of 14 competitor entries are self-references or subsidiaries:
- "PG&E", "PG&E Utility", "PG&E Recovery Funding LLC", "PG&E Wildfire Recovery Funding LLC"
- "Pacific Gas and Electric Company", "Pacific Gas and Electric (PG&E)", "Pacific Gas and Electric (PG&E Utility)", "Pacific Gas and Electric (PG&E) Utility", "Pacific Gas and Electric (The Utility)", "Pacific Gas and Electric (Utility)"
- "Pacific Generation LLC" (PG&E subsidiary)
- "CAISO" duplicated as "California Independent System Operator (CAISO)"
- Only legitimate external entry: "San Diego Gas & Electric Company"

**PayPal (PYPL):** 7 of 9 entries are subsidiaries or acquisitions:
- "PayPal (Europe)", "PayPal Credit Pty Limited", "PayPal Pte. Ltd.", "PayPal, Inc." — all PayPal subsidiaries
- "Venmo" — PayPal subsidiary
- "Paidy" — acquired by PayPal in 2021
- "TIO Networks" — acquired by PayPal in 2017
- Only legitimate competitors: "Block, Inc." and "eBay"

**Microsoft (MSFT):** 8 entries are acquisitions, not competitors:
- "GitHub" (acquired 2018), "LinkedIn" (acquired 2016)
- "Nuance" and "Nuance Communications, Inc." (acquired 2022, also a duplicate)
- "Activision Blizzard, Inc." (acquired 2023)
- "Bethesda Softworks LLC" and "ZeniMax Media Inc." (acquired 2021)
- "Microsoft Mobile Oy" (Microsoft's own subsidiary, former Nokia unit)

**NVIDIA (NVDA):** ~22 of 55 entries are suppliers, manufacturers, or service providers:
- Contract manufacturers: "Hon Hai" / "Hon Hai Precision Industry Co." (Foxconn), "Jabil Inc.", "Flex Ltd.", "Fabrinet", "Wistron Corporation"
- Foundry partner: "Taiwan Semiconductor Manufacturing Company Limited"
- Packaging/test: "Siliconware Precision Industries", "Amkor Technology", "King Yuan Electronics"
- PCB/substrate: "Ibiden Co. Ltd.", "Unimicron Technology", "Kinsus Interconnect Technology"
- Other: "Universal Scientific Industrial", "Applied Optoelectronics", "Coherent, Inc.", "JDS Uniphase Corp.", "Lumentum Holdings", "Chroma ATE Inc."
- Non-competitors: "Booz Allen Hamilton Inc." (consulting), "Cooley LLP" (law firm), "Lockheed Missiles and Space Company" (customer)
- Also duplicates: "AMD" / "Advanced Micro Devices, Inc.", "Hon Hai" / "Hon Hai Precision Industry Co.", "Samsung" / "Samsung Electronics Co. Ltd" / "Samsung Semiconductor, Inc.", "SoftBank" / "SoftBank Group Corp."

**Amazon (AMZN):** All 4 entries are acquisitions/investments, not competitors:
- "1Life Healthcare, Inc. (One Medical)" — acquired by Amazon
- "MGM Holdings Inc." — acquired by Amazon
- "Rivian" — Amazon investment
- "iRobot Corporation" — acquisition target

**Apple (AAPL):** 2 questionable entries:
- "Appiphany Technologies Corporation" — obscure, unclear relevance
- "Verde Bio Holdings, Inc." — oil/gas company, completely unrelated

### 2. PayPal CUSIP is wrong

The Company node for PayPal has CUSIP "1633917" which is actually its CIK number. The correct CUSIP is "70450Y103".

### 3. Duplicate Company nodes for the same entity

The database has 145 Company nodes but only 6 represent real filing companies. Many are fragmented duplicates created by the KGBuilder:
- PG&E has ~14 variant nodes: "PG&E Corporation", "PG&E Utility", "Pacific Gas and Electric (Utility)", "Pacific Gas and Electric (PG&E)", "PG&E", etc.
- Microsoft has 3 variant nodes: "Microsoft Corporation", "Microsoft (Windows)", "Microsoft (Xbox)"
- PayPal has subsidiary nodes labeled as Company: "PayPal, Inc.", "PayPal (Europe)", "PayPal Pte. Ltd."

These fragments are then incorrectly linked via COMPETES_WITH back to the parent company.

## Moderate

### 4. Product near-duplicates from LLM extraction

The pipeline extracted different phrasings of the same product from different sections of the 10-K filings. Examples:

| Cluster | Entries | Count |
|---------|---------|-------|
| Buy Now Pay Later | "Buy Now Pay Later", "Buy Now, Pay Later", "Buy Now Pay Later / Installment Methods" | 3 |
| H100 | "H100 GPU", "H100 Integrated Circuit", "H100 integrated circuits", "NVIDIA H100 Tensor Core GPU" | 4 |
| Omniverse | "NVIDIA Omniverse", "NVIDIA Omniverse Avatar", "NVIDIA Omniverse Enterprise", "Omniverse Cloud", "Omniverse Avatar Cloud Engine", "Omniverse Enterprise software" | 6 |
| Cryptocurrency | "Cryptocurrency Custodial Services", "Cryptocurrency Offerings", "Cryptocurrency Products", "Cryptocurrency Purchase and Sale", "Cryptocurrency Services", "Cryptocurrency Transactions" | 6 |
| Consumer Credit/Lending | "Consumer Credit Products", "Consumer Loans", "Credit Products", "Consumer Installment Loans", "Consumer Short-Term Installment Loan", "U.S. Installment Loan Products", etc. | 16 |
| PayPal/Venmo Branded Credit | "PayPal Branded Consumer Credit Products", "PayPal Consumer Credit", "PayPal Credit", "PayPal Consumer Credit Card", "Venmo Branded Credit Products", "Venmo Consumer Credit", etc. | 9 |
| RTX GPUs | "GeForce RTX 40 Series", "GeForce RTX GPUs", "NVIDIA RTX", "NVIDIA RTX GPUs", "NVIDIA RTX Platform", "NVIDIA Ampere Architecture RTX GPUs", "Quadro/NVIDIA RTX GPUs" | 7+ |
| Diablo Canyon | "Diablo Canyon Nuclear Generation Facility", "Diablo Canyon Nuclear Power Plant", "Diablo Canyon Unit 1", "Diablo Canyon Unit 2" | 4 |
| Gas Services (PG&E) | "Backbone Gas Transmission Service", "Gas Delivery Service", "Gas Service", "Gas Storage Service", "Gas Transmission and Storage" | 5 |
| Generic AI | "AI Cloud Services", "AI Innovations", "AI Platform Services", "AI Products and Services", "AI Services", "AI Technologies and Associated Products", "AI and Machine Learning Platform", "AI-powered Productivity Services" | 8 |
| Merchant Financing | "Merchant Finance Offerings", "Merchant Financing", "Merchant Loans and Advances" + 4 country-specific variants | 7 |
| Xoom | "Xoom", "Xoom International Money Transfer" | 2 |
| Wearables | "Accessories", "Wearables and Accessories", "Wearables, Home and Accessories" | 3 |

### 5. Products that are not products

~18 entries are licensing agreements, internal programs, or financial instruments:

**Licensing/contracting terms:**
- "Enterprise Agreement", "Microsoft Customer Agreement", "Microsoft Online Subscription Agreement", "Microsoft Products and Services Agreement", "Microsoft Services Provider License Agreement"
- "On-Premises Software Licenses", "Open Value", "Select Plus", "Software Assurance", "Software Products and Services Financing Program", "Volume Licensing Programs"

**Internal programs:**
- "AI Skills Initiative", "CARE Program", "Customer Protection Programs", "Deep Learning Institute", "Inception Program", "Purchase Protection Program", "Seller Protection Program"

**Financial instruments:**
- "Senior Secured Recovery Bonds", "Senior Secured Recovery Bonds Series 2022-A", "Senior Secured Recovery Bonds Series 2022-B"

### 6. Risk factor near-duplicates

~13 pairs/groups with near-identical names:

| Pair/Group | Entries |
|------------|---------|
| Tax liabilities | "Additional Tax Liabilities Risk" / "Additional Tax Liabilities and Collection Obligations" |
| Cross-border data | "Cross-Border Data Transfer Restrictions" / "Cross-Border Data Transfer Risk" |
| Crypto mining | "Cryptocurrency Mining Demand Risk" / "Cryptocurrency Mining Demand Volatility" |
| Data privacy (x4) | "Data Privacy and Security" / "Data Privacy and Security Obligations" / "Data Privacy and Security Risk" / "Data privacy and security regulations" |
| Distributed gen | "Distributed Generation and Energy Storage Competition" / "Distributed Generation and Energy Storage Viability" |
| Environmental | "Environmental Remediation Liabilities" / "Environmental Remediation Liability Risk" |
| IP infringement | "Intellectual Property Infringement" / "Intellectual Property Infringement Claims" |
| IP protection | "Intellectual Property Protection Risk" / "Intellectual property protection" |
| Legal compliance | "Legal and Regulatory Compliance Risk" / "Legal and Regulatory Compliance Risks" |
| Litigation | "Litigation and Regulatory Proceedings" / "Litigation and Regulatory Risk" |
| Nation-state | "Nation-State Cyber Attack Risk" / "Nation-State Cyber Attacks" |
| Wildfire fund | "Wildfire Fund Contribution Obligations" / "Wildfire Fund Contribution Risk" |
| Wildfire mitigation | "Wildfire Mitigation Cost Recovery Risk" / "Wildfire Mitigation Cost Risk" |
| Business disruption | "Business Processes and Information Systems Disruption" / "Business process and information systems interruption" |
| Product defects | "Product Defect Risk" / "Product defects" |

### 7. Inconsistent casing in risk factor names

Most risk names use Title Case but several use lowercase:
- "Business process and information systems interruption"
- "Competition in markets"
- "Cybersecurity and data breaches"
- "Data privacy and security regulations"
- "Executive and key employee retention"
- "Intellectual property protection"
- "Product defects"

## Minor

### 8. Asset manager name formatting

Names use a mix of ALL CAPS and Title Case, inherited from SEC 13-F filings:
- ALL CAPS (11): ALLIANCEBERNSTEIN L.P., AMERIPRISE FINANCIAL INC, AMUNDI, etc.
- Title Case (4): Bank of New York Mellon Corp, Berkshire Hathaway Inc, BlackRock Inc., Capital World Investors
- Inconsistent trailing punctuation: "BlackRock Inc." (with period) vs "AMERIPRISE FINANCIAL INC" (without)
- SEC filing artifacts in names: "BANK OF AMERICA CORP /DE/", "WELLS FARGO & COMPANY/MN"

### 9. CUSIP formatting inconsistencies

- Amazon CUSIP "23135106" — 8 chars, may be missing leading zero (standard is 9 chars)
- NVIDIA CUSIP "067066G104" — 10 chars, appears to be ISIN-like format instead of 9-char CUSIP
- PG&E CUSIP "069331C908" — 10 chars, same issue

### 10. AssetManager property naming

The database uses `managerName` as the property key for asset manager names, while all other node types use `name`. This inconsistency complicates generic queries.
