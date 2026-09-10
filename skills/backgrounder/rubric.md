# Backgrounder rubric — decomposition of the goal

Root: **Carrie's goal is achieved** — the report is what she wants. Each node
consists of its children; children partition their parent (comprehensive and
non-redundant), so covering every leaf covers the goal. No implementation
particulars: the tree says what must be true, never how it is made true.

Use: mark, with Adam and Carrie, which nodes matter most. Focus follows.

Visual: published as the "Backgrounder Rubric" artifact.

```
Carrie's goal is achieved — the report is what she wants
├─ Content is right                    (what the report says)
│  ├─ Right person        — every claim concerns the intended person
│  ├─ Retrieval is right  — everything knowable from her sources is gathered
│  │  ├─ Correct sources        — every source that can bear is consulted
│  │  ├─ Correct queries        — asked every way the person can appear
│  │  ├─ Correct parsing        — results read faithfully, nothing mangled
│  │  └─ Correct error handling — failures surface; partial never passes
│  │                              as complete
│  ├─ Selection is right  — what matters is in; noise is out
│  ├─ Accuracy is right   — claims trace to sources; fact vs inference
│  └─ Limits are stated   — what sources can't see is declared
├─ Format is right                     (how the report is organized)
│  ├─ Structure she wants — the deliverable set, and how each is organized
│  └─ Templateized        — fixed in a template; cannot drift run to run
└─ Look and feel is right              (how the report presents)
   ├─ Matches her taste   — validated with her, not assumed
   └─ Templateized        — fixed in a template; cannot drift run to run
```

Partition logic, per branch:

- **Root** splits by the three aspects of any document: claims, organization,
  presentation.
- **Content** follows the life of a claim: whose it is (person), what could be
  said (retrieval), what is said (selection), said truly (accuracy), and the
  complement — what cannot be said (limits).
- **Retrieval** is Cliff's pipeline partition: where to look, what to ask,
  how to read, how failure behaves.
- **Format / Look and feel** each split on two orthogonal axes: the design is
  right (correctness) × the design cannot drift (stability, via template).
  Which artifacts she gets is the outermost level of structure, so
  "deliverables" lives inside the structure leaf rather than beside it.
```
