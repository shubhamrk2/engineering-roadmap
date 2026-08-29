/* Single source of truth for the drawing set. Every page reads this. */
window.SHEETS = [
  { g: 'Preflight', no: '00', t: 'The Plan',          f: 'index.html',       w: 'W00',     kw: 'roadmap schedule 12 week plan how to use progress' },
  { g: 'Preflight', no: '01', t: 'Machine Setup',     f: 'setup.html',       w: 'W00',     kw: 'install wsl node python java docker vscode corporate laptop proxy no admin' },
 
  { g: 'Build the product', no: '02', t: 'Languages',   f: 'programming.html', w: 'W01–02', kw: 'python javascript typescript java oop async types generics' },
  { g: 'Build the product', no: '03', t: 'Frontend',    f: 'frontend.html',    w: 'W03–04', kw: 'html css tailwind react nextjs hooks ssr rsc state' },
  { g: 'Build the product', no: '04', t: 'Backend',     f: 'backend.html',     w: 'W05–06', kw: 'fastapi express nestjs node middleware auth jwt di pydantic' },
  { g: 'Build the product', no: '05', t: 'APIs',        f: 'apis.html',        w: 'W05–06', kw: 'rest graphql webhooks openapi versioning idempotency http status' },
  { g: 'Build the product', no: '06', t: 'Databases',   f: 'databases.html',   w: 'W07',    kw: 'postgresql mongodb redis sql index transaction acid normalisation cache' },
 
  { g: 'Ship it and run it', no: '07', t: 'AWS',        f: 'aws.html',         w: 'W08–09', kw: 'ec2 s3 rds lambda eks iam vpc cloudwatch cloud aws' },
  { g: 'Ship it and run it', no: '08', t: 'Azure',      f: 'azure.html',       w: 'W09',    kw: 'azure vm blob aks entra vnet monitor functions mapping' },
  { g: 'Ship it and run it', no: '09', t: 'DevOps',     f: 'devops.html',      w: 'W10',    kw: 'git github actions docker kubernetes ci cd pipeline deploy' },
  { g: 'Ship it and run it', no: '10', t: 'Terraform',  f: 'terraform.html',   w: 'W10',    kw: 'terraform iac state module provider plan apply drift' },
  { g: 'Ship it and run it', no: '11', t: 'Messaging',  f: 'messaging.html',   w: 'W11',    kw: 'kafka rabbitmq queue topic partition consumer group exchange async events' },
 
  { g: 'Prove it',  no: '12', t: 'AI Engineering', f: 'ai.html',        w: 'W11',    kw: 'llm openai prompt engineering rag vector database embeddings agents tokens' },
  { g: 'Prove it',  no: '13', t: 'Projects',       f: 'projects.html',  w: 'W02–12', kw: 'projects portfolio capstone badgedesk build resume' },
  { g: 'Prove it',  no: '14', t: 'Drill Book',     f: 'interview.html', w: 'W12',    kw: 'interview questions system design behavioural star answers rounds' },
  { g: 'Prove it',  no: '15', t: 'DSA Drill',      f: 'dsa.html',       w: 'W01–12', kw: 'dsa data structures algorithms striver a2z arrays binary search linked list recursion graphs dynamic programming leetcode two pointer sliding window prefix sum' }
];