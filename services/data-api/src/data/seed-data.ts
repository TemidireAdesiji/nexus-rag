export const teamMembers = [
  {
    id: "tm-001",
    fullName: "Priya Vasudeva",
    title: "Managing Partner",
    biography:
      "Priya Vasudeva founded Nexus Capital Partners after a distinguished career spanning two decades in institutional finance and technology investing. She previously led the growth equity division at Meridian Ventures, where she orchestrated over $2.8 billion in deployments across enterprise software and digital infrastructure. Priya holds an MBA from INSEAD and serves on the advisory boards of three publicly traded technology firms.",
    specializations: [
      "Growth Equity",
      "Enterprise SaaS",
      "Board Governance",
      "Capital Markets Strategy",
    ],
  },
  {
    id: "tm-002",
    fullName: "Dominic Castellano",
    title: "Senior Partner, Investments",
    biography:
      "Dominic Castellano brings fifteen years of venture capital experience with a focus on Series B through pre-IPO rounds in cloud infrastructure and cybersecurity. Before joining Nexus, he was a Principal at Horizon Growth Fund where he identified and supported several unicorn-trajectory companies. Dominic holds a dual degree in Computer Science and Finance from Carnegie Mellon University and is a CFA charterholder.",
    specializations: [
      "Cloud Infrastructure",
      "Cybersecurity",
      "Late-Stage Venture",
      "Technical Due Diligence",
    ],
  },
  {
    id: "tm-003",
    fullName: "Liora Nakamura",
    title: "Partner, Sector Strategy",
    biography:
      "Liora Nakamura oversees sector-level research and thematic investment strategies at Nexus Capital Partners. She previously held senior analyst roles at Goldman Sachs and BlackRock, where she built quantitative models for technology sector allocation. Liora earned her PhD in Applied Mathematics from MIT and is widely published on the intersection of machine learning and financial modeling.",
    specializations: [
      "Quantitative Analysis",
      "Artificial Intelligence",
      "Sector Research",
      "Thematic Investing",
    ],
  },
  {
    id: "tm-004",
    fullName: "Marcus Odhiambo",
    title: "Vice President, Portfolio Operations",
    biography:
      "Marcus Odhiambo leads post-investment value creation initiatives, working directly with portfolio company leadership to accelerate revenue growth and operational efficiency. He previously served as COO at a Series C fintech startup that achieved a successful SPAC merger. Marcus holds an MBA from Wharton and brings expertise in organizational scaling, go-to-market optimization, and talent strategy.",
    specializations: [
      "Portfolio Operations",
      "Revenue Acceleration",
      "Organizational Design",
      "Fintech",
    ],
  },
  {
    id: "tm-005",
    fullName: "Elena Kowalski",
    title: "Principal, Emerging Technologies",
    biography:
      "Elena Kowalski focuses on early identification of transformative technology platforms, with particular depth in distributed systems, edge computing, and developer tooling. She joined Nexus from a leading Silicon Valley accelerator where she mentored over forty startups. Elena holds a Master of Engineering from Stanford and has filed three patents in distributed consensus algorithms.",
    specializations: [
      "Emerging Technologies",
      "Developer Platforms",
      "Edge Computing",
      "Early-Stage Scouting",
    ],
  },
];

export const investments = [
  {
    id: "inv-001",
    companyName: "Stratos Analytics",
    assetClass: "Series B Equity",
    capitalDeployed: 18500000,
    executionDate: new Date("2023-03-15"),
    currentStatus: "Active",
    sectors: ["Data Analytics", "Enterprise Software"],
  },
  {
    id: "inv-002",
    companyName: "VaultEdge Security",
    assetClass: "Series C Equity",
    capitalDeployed: 32000000,
    executionDate: new Date("2022-11-08"),
    currentStatus: "Active",
    sectors: ["Cybersecurity", "Cloud Infrastructure"],
  },
  {
    id: "inv-003",
    companyName: "Plyra Health",
    assetClass: "Series A Equity",
    capitalDeployed: 7200000,
    executionDate: new Date("2024-01-22"),
    currentStatus: "Active",
    sectors: ["Digital Health", "Artificial Intelligence"],
  },
  {
    id: "inv-004",
    companyName: "Conduit Financial",
    assetClass: "Growth Equity",
    capitalDeployed: 45000000,
    executionDate: new Date("2021-07-30"),
    currentStatus: "Partially Exited",
    sectors: ["Fintech", "Payments Infrastructure"],
  },
  {
    id: "inv-005",
    companyName: "Tessera Dev Tools",
    assetClass: "Seed Extension",
    capitalDeployed: 3800000,
    executionDate: new Date("2024-06-10"),
    currentStatus: "Active",
    sectors: ["Developer Platforms", "DevOps"],
  },
  {
    id: "inv-006",
    companyName: "Omnilayer Networks",
    assetClass: "Series B Equity",
    capitalDeployed: 22000000,
    executionDate: new Date("2023-09-05"),
    currentStatus: "Active",
    sectors: ["Edge Computing", "Telecommunications"],
  },
  {
    id: "inv-007",
    companyName: "Brevity AI",
    assetClass: "Series A Equity",
    capitalDeployed: 12500000,
    executionDate: new Date("2024-03-18"),
    currentStatus: "Active",
    sectors: ["Artificial Intelligence", "Natural Language Processing"],
  },
  {
    id: "inv-008",
    companyName: "Arcline Logistics",
    assetClass: "Growth Equity",
    capitalDeployed: 28000000,
    executionDate: new Date("2022-04-12"),
    currentStatus: "Exited",
    sectors: ["Supply Chain", "Enterprise Software"],
  },
];

export const sectors = [
  {
    id: "sec-001",
    verticalName: "Enterprise Cloud Infrastructure",
    overview:
      "Enterprise cloud infrastructure encompasses the foundational compute, storage, and networking layers that power modern business applications. This vertical has matured beyond basic IaaS into sophisticated multi-cloud orchestration, serverless architectures, and infrastructure-as-code platforms. Annual market growth remains above 20% as organizations continue migrating workloads from on-premises environments.",
    emergingTrends: [
      "Multi-cloud governance frameworks",
      "FinOps and cloud cost optimization",
      "Confidential computing enclaves",
      "Infrastructure-as-code standardization",
    ],
    investmentTeam: ["Dominic Castellano", "Elena Kowalski"],
  },
  {
    id: "sec-002",
    verticalName: "Applied Artificial Intelligence",
    overview:
      "Applied AI focuses on translating foundational model capabilities into domain-specific enterprise solutions. This vertical spans intelligent document processing, conversational interfaces, predictive maintenance, and decision automation. The market is rapidly evolving from experimental pilots to production-grade deployments, with particular momentum in regulated industries seeking compliant AI implementations.",
    emergingTrends: [
      "Retrieval-augmented generation systems",
      "Domain-specific fine-tuning",
      "AI governance and compliance tooling",
      "Agentic workflow orchestration",
    ],
    investmentTeam: ["Liora Nakamura", "Elena Kowalski"],
  },
  {
    id: "sec-003",
    verticalName: "Cybersecurity and Digital Trust",
    overview:
      "The cybersecurity vertical addresses the expanding attack surface created by digital transformation, remote work, and IoT proliferation. Investment opportunities span identity management, zero-trust architecture, threat intelligence platforms, and security operations automation. Regulatory pressure and rising breach costs continue to drive enterprise security budgets upward at double-digit rates.",
    emergingTrends: [
      "Post-quantum cryptography readiness",
      "AI-powered threat detection",
      "Software supply chain security",
      "Decentralized identity frameworks",
    ],
    investmentTeam: ["Dominic Castellano", "Priya Vasudeva"],
  },
  {
    id: "sec-004",
    verticalName: "Financial Technology Infrastructure",
    overview:
      "Fintech infrastructure encompasses the middleware, APIs, and platforms that enable modern financial services. This vertical has shifted from consumer-facing disruption to B2B infrastructure plays, including banking-as-a-service, embedded finance, real-time payments, and regulatory technology. Revenue models are predominantly transaction-based or platform fees, offering strong recurring revenue characteristics.",
    emergingTrends: [
      "Embedded lending and insurance platforms",
      "Real-time cross-border settlement",
      "Open banking API ecosystems",
      "Programmable compliance engines",
    ],
    investmentTeam: ["Marcus Odhiambo", "Priya Vasudeva"],
  },
  {
    id: "sec-005",
    verticalName: "Developer Ecosystem and Tooling",
    overview:
      "The developer ecosystem vertical encompasses tools, platforms, and services that improve software development velocity and reliability. This includes CI/CD pipelines, observability platforms, API management, low-code frameworks, and developer experience tooling. The market is driven by the growing global developer population and increasing complexity of modern software architectures.",
    emergingTrends: [
      "AI-assisted code generation and review",
      "Internal developer platform standardization",
      "WebAssembly adoption in server environments",
      "Unified observability with AI correlation",
    ],
    investmentTeam: ["Elena Kowalski", "Liora Nakamura"],
  },
];

export const consultations = [
  {
    id: "con-001",
    subject: "Q4 Portfolio Performance Review and 2025 Outlook",
    scheduledDate: new Date("2025-01-15T10:00:00Z"),
    participants: [
      "Priya Vasudeva",
      "Dominic Castellano",
      "Liora Nakamura",
      "Marcus Odhiambo",
    ],
    synopsis:
      "Comprehensive review of Q4 2024 portfolio performance across all active positions. Discussion covered mark-to-market adjustments for three growth-stage holdings, preliminary 2025 deployment targets, and sector allocation rebalancing. The team agreed to increase exposure to applied AI infrastructure and reduce concentration in late-stage fintech positions.",
  },
  {
    id: "con-002",
    subject: "VaultEdge Security - Series D Co-Investment Evaluation",
    scheduledDate: new Date("2025-02-03T14:30:00Z"),
    participants: ["Dominic Castellano", "Priya Vasudeva"],
    synopsis:
      "Evaluated the opportunity to participate in VaultEdge Security's upcoming Series D round at a $1.2B pre-money valuation. Reviewed updated financials showing 140% net revenue retention and $48M ARR. Discussed competitive positioning against CrowdStrike and Palo Alto Networks. Decision to proceed with a $15M follow-on investment contingent on favorable terms.",
  },
  {
    id: "con-003",
    subject: "Emerging Technology Landscape - Edge Computing Deep Dive",
    scheduledDate: new Date("2025-02-18T09:00:00Z"),
    participants: ["Elena Kowalski", "Liora Nakamura", "Dominic Castellano"],
    synopsis:
      "Elena presented research findings on the edge computing market evolution, covering key architectural shifts from centralized cloud to distributed edge nodes. Identified three investment themes: edge-native application platforms, telco-edge partnerships, and industrial IoT edge gateways. The team prioritized building a pipeline of Series A/B candidates in the edge-native platform category.",
  },
  {
    id: "con-004",
    subject: "LP Advisory Committee - Annual Strategy Presentation",
    scheduledDate: new Date("2025-03-05T11:00:00Z"),
    participants: [
      "Priya Vasudeva",
      "Marcus Odhiambo",
      "Liora Nakamura",
    ],
    synopsis:
      "Preparation session for the upcoming LP Advisory Committee meeting. Reviewed fund performance metrics, including 2.4x gross MOIC on Fund III vintage and top-quartile DPI. Finalized the narrative around thematic pivots toward AI infrastructure and developer tooling. Marcus presented portfolio company operational metrics demonstrating value creation across revenue, headcount, and margin expansion.",
  },
  {
    id: "con-005",
    subject: "Brevity AI - Board Observer Session and Milestone Review",
    scheduledDate: new Date("2025-03-20T15:00:00Z"),
    participants: ["Liora Nakamura", "Elena Kowalski"],
    synopsis:
      "Post-board meeting debrief on Brevity AI's progress toward Series B readiness. The company has reached $5.2M ARR with 85% gross margins and secured three enterprise lighthouse customers. Discussed the product roadmap for multi-modal capabilities and the competitive landscape with well-funded incumbents. Recommended introducing the company to two strategic partners in the Nexus network.",
  },
  {
    id: "con-006",
    subject: "Talent Strategy and Organizational Scaling Workshop",
    scheduledDate: new Date("2025-04-02T10:00:00Z"),
    participants: [
      "Marcus Odhiambo",
      "Priya Vasudeva",
      "Dominic Castellano",
      "Liora Nakamura",
      "Elena Kowalski",
    ],
    synopsis:
      "Full team workshop focused on strengthening the firm's operational support capabilities. Marcus outlined a framework for embedding fractional C-suite talent into portfolio companies during critical scaling phases. The team discussed expanding the operating partner network to include specialists in product-led growth, international expansion, and enterprise sales motion design. Action items include formalizing an operating playbook by end of Q2.",
  },
];
