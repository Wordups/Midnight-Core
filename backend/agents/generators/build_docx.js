#!/usr/bin/env node
/**
 * Trace Agent docx generator — invoked via subprocess from
 * backend/agents/generators/docx_generator.py.
 *
 * Reads a JSON spec from stdin describing the document to build, writes
 * the rendered .docx bytes to the path given as argv[2], and prints a
 * single-line JSON result to stdout. Errors land on stderr and a
 * non-zero exit code.
 *
 * Why Node + docx-js rather than python-docx: docx-js produces native
 * Word run/paragraph trees with no markdown intermediate, which is the
 * failure mode we kept tripping on policy generation.
 *
 * Spec shape (stdin):
 *   {
 *     "title":  "Document title (rendered as Heading 1)",
 *     "subtitle": "Optional subtitle line below the title",
 *     "frontMatter": [{"label": "Owner", "value": "..."}, ...],
 *     "sections": [
 *       {
 *         "heading": "1. Purpose and Scope",
 *         "level":   1,   // 1 = Heading 1, 2 = Heading 2, etc.
 *         "blocks": [
 *           {"kind": "paragraph", "text": "Inline text..."},
 *           {"kind": "bullets",   "items": ["one", "two"]},
 *           {"kind": "ordered",   "items": ["first", "second"]},
 *           {"kind": "callout",   "text": "Auditor expectation: ..."}
 *         ]
 *       }
 *     ]
 *   }
 *
 * The spec is intentionally narrow — Trace Agent's LLM call (step 8,
 * build_script) produces this JSON shape, NOT raw docx-js code. That
 * keeps the LLM output verifiable.
 */
'use strict';

const fs = require('fs');
const path = require('path');

let docxLib;
try {
  docxLib = require('docx');
} catch (err) {
  process.stderr.write(
    'docx package not installed. Run `npm install` in ' +
    'backend/agents/generators/ before invoking this script.\n'
  );
  process.exit(2);
}

const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
} = docxLib;

const HEADING_BY_LEVEL = {
  1: HeadingLevel.HEADING_1,
  2: HeadingLevel.HEADING_2,
  3: HeadingLevel.HEADING_3,
  4: HeadingLevel.HEADING_4,
  5: HeadingLevel.HEADING_5,
  6: HeadingLevel.HEADING_6,
};

// Strip residual markdown markers from any value before it lands in a run.
// Defense-in-depth — the LLM is told to emit plain text but if it slips a
// `**bold**` or `## heading` in, we don't pass it through verbatim.
function scrubMarkdown(text) {
  if (text == null) return '';
  let s = String(text);
  s = s.replace(/`{1,3}([^`]+)`{1,3}/g, '$1');
  s = s.replace(/\*\*\*([^*]+)\*\*\*/g, '$1');
  s = s.replace(/\*\*([^*]+)\*\*/g, '$1');
  s = s.replace(/__([^_]+)__/g, '$1');
  s = s.replace(/(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)/g, '$1');
  s = s.replace(/(?<!_)_(?!_)([^_\n]+?)(?<!_)_(?!_)/g, '$1');
  s = s.replace(/~~([^~]+)~~/g, '$1');
  s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  s = s.replace(/^\s*#{1,6}\s+/gm, '');
  s = s.replace(/^\s*[>*+\-]\s+/gm, '');
  return s;
}

function makeParagraph(block) {
  const text = scrubMarkdown(block.text || '');
  return new Paragraph({
    children: [new TextRun(text)],
    spacing: { after: 120 },
  });
}

function makeBullet(item, ordered) {
  const text = scrubMarkdown(item);
  return new Paragraph({
    children: [new TextRun(text)],
    bullet: ordered ? undefined : { level: 0 },
    numbering: ordered ? { reference: 'default-numbering', level: 0 } : undefined,
    spacing: { after: 80 },
  });
}

function makeCallout(block) {
  const text = scrubMarkdown(block.text || '');
  // Render as a single-cell shaded table — distinct from body paragraphs
  // without depending on docx-js style packs (which vary by version).
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            children: [new Paragraph({ children: [new TextRun({ text, bold: true })] })],
            shading: { fill: 'EEEEEE' },
            borders: {
              top:    { style: BorderStyle.SINGLE, size: 4, color: '999999' },
              bottom: { style: BorderStyle.SINGLE, size: 4, color: '999999' },
              left:   { style: BorderStyle.SINGLE, size: 4, color: '999999' },
              right:  { style: BorderStyle.SINGLE, size: 4, color: '999999' },
            },
          }),
        ],
      }),
    ],
  });
}

function makeSectionHeading(section) {
  const level = HEADING_BY_LEVEL[section.level || 1] || HeadingLevel.HEADING_1;
  return new Paragraph({
    text: scrubMarkdown(section.heading || ''),
    heading: level,
    spacing: { before: 280, after: 140 },
  });
}

function makeFrontMatterTable(rows) {
  if (!rows || rows.length === 0) return null;
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: rows.map(r => new TableRow({
      children: [
        new TableCell({
          width: { size: 30, type: WidthType.PERCENTAGE },
          children: [new Paragraph({ children: [new TextRun({ text: scrubMarkdown(r.label || ''), bold: true })] })],
        }),
        new TableCell({
          width: { size: 70, type: WidthType.PERCENTAGE },
          children: [new Paragraph({ children: [new TextRun(scrubMarkdown(r.value || ''))] })],
        }),
      ],
    })),
  });
}

function buildDocChildren(spec) {
  const out = [];
  if (spec.title) {
    out.push(new Paragraph({
      text: scrubMarkdown(spec.title),
      heading: HeadingLevel.TITLE,
      alignment: AlignmentType.LEFT,
      spacing: { after: 120 },
    }));
  }
  if (spec.subtitle) {
    out.push(new Paragraph({
      children: [new TextRun({ text: scrubMarkdown(spec.subtitle), italics: true })],
      spacing: { after: 200 },
    }));
  }
  const fm = makeFrontMatterTable(spec.frontMatter || []);
  if (fm) {
    out.push(fm);
    out.push(new Paragraph({ children: [new TextRun('')], spacing: { after: 200 } }));
  }

  for (const section of spec.sections || []) {
    out.push(makeSectionHeading(section));
    for (const block of section.blocks || []) {
      const kind = block.kind || 'paragraph';
      if (kind === 'paragraph') {
        out.push(makeParagraph(block));
      } else if (kind === 'bullets') {
        for (const item of block.items || []) out.push(makeBullet(item, false));
      } else if (kind === 'ordered') {
        for (const item of block.items || []) out.push(makeBullet(item, true));
      } else if (kind === 'callout') {
        out.push(makeCallout(block));
      } else {
        // Unknown block kinds fall through as plain paragraphs so the
        // generator never silently drops content.
        out.push(makeParagraph({ text: JSON.stringify(block) }));
      }
    }
  }
  return out;
}

async function main() {
  const outPath = process.argv[2];
  if (!outPath) {
    process.stderr.write('usage: node build_docx.js <output-path>  (spec JSON on stdin)\n');
    process.exit(2);
  }

  let raw = '';
  process.stdin.setEncoding('utf8');
  for await (const chunk of process.stdin) raw += chunk;

  let spec;
  try {
    spec = JSON.parse(raw);
  } catch (err) {
    process.stderr.write(`invalid spec JSON on stdin: ${err.message}\n`);
    process.exit(3);
  }

  let doc;
  try {
    doc = new Document({
      creator: 'Midnight Trace Agent',
      title: spec.title || 'Untitled Document',
      sections: [
        {
          properties: {},
          children: buildDocChildren(spec),
        },
      ],
      numbering: {
        config: [
          {
            reference: 'default-numbering',
            levels: [
              {
                level: 0,
                format: 'decimal',
                text: '%1.',
                alignment: AlignmentType.START,
              },
            ],
          },
        ],
      },
    });
  } catch (err) {
    process.stderr.write(`docx-js Document() build failed: ${err.message}\n`);
    process.exit(4);
  }

  let buffer;
  try {
    buffer = await Packer.toBuffer(doc);
  } catch (err) {
    process.stderr.write(`Packer.toBuffer() failed: ${err.message}\n`);
    process.exit(5);
  }

  try {
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, buffer);
  } catch (err) {
    process.stderr.write(`failed to write ${outPath}: ${err.message}\n`);
    process.exit(6);
  }

  const result = {
    ok: true,
    docx_path: outPath,
    bytes: buffer.length,
    section_count: (spec.sections || []).length,
  };
  process.stdout.write(JSON.stringify(result) + '\n');
}

main().catch(err => {
  process.stderr.write(`unhandled error: ${err && err.stack ? err.stack : err}\n`);
  process.exit(1);
});
