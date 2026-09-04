from typing import Dict, Any

MODERN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{{ name }} - Resume</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background: #ffffff;
    line-height: 1.45;
    padding: 36px 42px;
    font-size: 11pt;
  }
  header {
    border-bottom: 2px solid #2563eb;
    padding-bottom: 12px;
    margin-bottom: 16px;
  }
  h1 {
    font-size: 24pt;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.5px;
  }
  .title {
    font-size: 13pt;
    font-weight: 600;
    color: #2563eb;
    margin-top: 2px;
  }
  .contact {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 9.5pt;
    color: #64748b;
    margin-top: 6px;
  }
  .contact span { display: inline-flex; align-items: center; }
  .section {
    margin-bottom: 15px;
  }
  .section-title {
    font-size: 11pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #1e3a8a;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 3px;
    margin-bottom: 8px;
  }
  .summary-text {
    font-size: 10pt;
    color: #334155;
    text-align: justify;
  }
  .item {
    margin-bottom: 10px;
  }
  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }
  .item-title {
    font-weight: 700;
    font-size: 10.5pt;
    color: #0f172a;
  }
  .item-subtitle {
    font-weight: 600;
    color: #475569;
    font-size: 10pt;
  }
  .item-date {
    font-size: 9pt;
    color: #64748b;
    font-style: italic;
  }
  ul {
    list-style-type: square;
    margin-left: 18px;
    margin-top: 4px;
  }
  li {
    font-size: 9.5pt;
    color: #334155;
    margin-bottom: 3px;
  }
  .skills-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px 16px;
  }
  .skill-row {
    font-size: 9.5pt;
  }
  .skill-category {
    font-weight: 700;
    color: #0f172a;
  }
  .skill-items {
    color: #475569;
  }
  .tech-tag {
    display: inline-block;
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 8.5pt;
    margin-right: 4px;
  }
  @page {
    size: A4;
    margin: 12mm 10mm;
  }
</style>
</head>
<body>
  <header>
    <h1>{{ name }}</h1>
    <div class="title">{{ title }}</div>
    <div class="contact">
      {% if contact %}
        {% if contact.email %}<span>✉ {{ contact.email }}</span>{% endif %}
        {% if contact.phone %}<span>☎ {{ contact.phone }}</span>{% endif %}
        {% if contact.location %}<span>📍 {{ contact.location }}</span>{% endif %}
        {% if contact.linkedin %}<span>🔗 {{ contact.linkedin }}</span>{% endif %}
        {% if contact.github %}<span>🐙 {{ contact.github }}</span>{% endif %}
        {% if contact.portfolio %}<span>🌐 {{ contact.portfolio }}</span>{% endif %}
      {% endif %}
    </div>
  </header>

  {% if summary %}
  <div class="section">
    <div class="section-title">Professional Summary</div>
    <div class="summary-text">{{ summary }}</div>
  </div>
  {% endif %}

  {% if skills and skills|length > 0 %}
  <div class="section">
    <div class="section-title">Technical Skills</div>
    <div class="skills-grid">
      {% for s in skills %}
      <div class="skill-row">
        <span class="skill-category">{{ s.category }}:</span>
        <span class="skill-items">{{ s['items']|join(', ') if s['items'] else '' }}</span>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if experience and experience|length > 0 %}
  <div class="section">
    <div class="section-title">Professional Experience</div>
    {% for exp in experience %}
    <div class="item">
      <div class="item-header">
        <div>
          <span class="item-title">{{ exp.role }}</span>
          <span class="item-subtitle"> | {{ exp.company }}</span>
          {% if exp.location %}<span style="font-size: 9pt; color: #64748b;"> ({{ exp.location }})</span>{% endif %}
        </div>
        <div class="item-date">{{ exp.duration }}</div>
      </div>
      <ul>
        {% for b in exp.bullets %}
        <li>{{ b }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if projects and projects|length > 0 %}
  <div class="section">
    <div class="section-title">Key Projects</div>
    {% for proj in projects %}
    <div class="item">
      <div class="item-header">
        <div>
          <span class="item-title">{{ proj.name }}</span>
          {% if proj.link %}<a href="{{ proj.link }}" style="font-size: 8.5pt; color: #2563eb; text-decoration: none;"> [Link]</a>{% endif %}
        </div>
        <div class="item-date">
          {% for t in (proj.technologies or []) %}<span class="tech-tag">{{ t }}</span>{% endfor %}
        </div>
      </div>
      {% if proj.description %}<p style="font-size: 9.5pt; color: #475569; margin-top: 2px;">{{ proj.description }}</p>{% endif %}
      <ul>
        {% for b in (proj.bullets or proj.highlights or []) %}
        <li>{{ b }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if education and education|length > 0 %}
  <div class="section">
    <div class="section-title">Education</div>
    {% for edu in education %}
    <div class="item">
      <div class="item-header">
        <div>
          <span class="item-title">{{ edu.degree }}</span>
          <span class="item-subtitle"> | {{ edu.institution }}</span>
        </div>
        <div class="item-date">{{ edu.year }}</div>
      </div>
      {% if edu.details %}<p style="font-size: 9pt; color: #64748b; margin-top: 1px;">{{ edu.details }}</p>{% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}
</body>
</html>
"""

MINIMAL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{{ name }} - Minimalist Resume</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Times New Roman', Times, serif;
    color: #111;
    background: #fff;
    line-height: 1.4;
    padding: 32px 38px;
    font-size: 11pt;
  }
  header { text-align: center; margin-bottom: 14px; }
  h1 { font-size: 22pt; font-weight: normal; text-transform: uppercase; letter-spacing: 2px; }
  .title { font-size: 11pt; font-style: italic; color: #444; margin-top: 2px; }
  .contact { font-size: 9pt; color: #333; margin-top: 4px; word-spacing: 2px; }
  .section { margin-bottom: 12px; }
  .section-title {
    font-size: 10pt;
    font-weight: bold;
    text-transform: uppercase;
    border-bottom: 1px solid #333;
    padding-bottom: 2px;
    margin-bottom: 6px;
    letter-spacing: 1.5px;
  }
  .item-header { display: flex; justify-content: space-between; font-size: 10.5pt; font-weight: bold; }
  .item-date { font-weight: normal; font-size: 9.5pt; }
  .item-sub { font-style: italic; font-size: 10pt; color: #333; margin-bottom: 2px; }
  ul { list-style-type: disc; margin-left: 18px; margin-top: 3px; }
  li { font-size: 9.5pt; margin-bottom: 2px; text-align: justify; }
  .skill-line { font-size: 9.5pt; margin-bottom: 2px; }
  @page { size: A4; margin: 12mm 10mm; }
</style>
</head>
<body>
  <header>
    <h1>{{ name }}</h1>
    <div class="title">{{ title }}</div>
    <div class="contact">
      {% if contact %}
        {{ contact.location }} &bull; {{ contact.email }} &bull; {{ contact.phone }}
        {% if contact.linkedin %}&bull; {{ contact.linkedin }}{% endif %}
        {% if contact.github %}&bull; {{ contact.github }}{% endif %}
      {% endif %}
    </div>
  </header>

  {% if summary %}
  <div class="section">
    <div class="section-title">Summary</div>
    <p style="font-size: 9.5pt; text-align: justify;">{{ summary }}</p>
  </div>
  {% endif %}

  {% if experience and experience|length > 0 %}
  <div class="section">
    <div class="section-title">Experience</div>
    {% for exp in experience %}
    <div style="margin-bottom: 8px;">
      <div class="item-header">
        <span>{{ exp.company }}</span>
        <span class="item-date">{{ exp.duration }}</span>
      </div>
      <div class="item-sub">{{ exp.role }} - {{ exp.location }}</div>
      <ul>
        {% for b in exp.bullets %}<li>{{ b }}</li>{% endfor %}
      </ul>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if projects and projects|length > 0 %}
  <div class="section">
    <div class="section-title">Projects</div>
    {% for proj in projects %}
    <div style="margin-bottom: 8px;">
      <div class="item-header">
        <span>{{ proj.name }}</span>
        <span class="item-date" style="font-size: 8.5pt;">{{ (proj.technologies or [])|join(', ') }}</span>
      </div>
      <ul>
        {% for b in (proj.bullets or proj.highlights or []) %}<li>{{ b }}</li>{% endfor %}
      </ul>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if skills and skills|length > 0 %}
  <div class="section">
    <div class="section-title">Technical Skills</div>
    {% for s in skills %}
    <div class="skill-line"><strong>{{ s.category }}:</strong> {{ s['items']|join(', ') if s['items'] else '' }}</div>
    {% endfor %}
  </div>
  {% endif %}

  {% if education and education|length > 0 %}
  <div class="section">
    <div class="section-title">Education</div>
    {% for edu in education %}
    <div class="item-header">
      <span>{{ edu.institution }}</span>
      <span class="item-date">{{ edu.year }}</span>
    </div>
    <div class="item-sub">{{ edu.degree }} {% if edu.details %}- {{ edu.details }}{% endif %}</div>
    {% endfor %}
  </div>
  {% endif %}
</body>
</html>
"""

TEMPLATES = {
    "modern": MODERN_TEMPLATE,
    "minimal": MINIMAL_TEMPLATE
}
