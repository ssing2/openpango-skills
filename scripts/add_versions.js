const fs = require('fs');
const path = require('path');

const skillsDir = path.join(__dirname, '..', 'skills');
const skills = fs.readdirSync(skillsDir).filter(f => fs.statSync(path.join(skillsDir, f)).isDirectory());

skills.forEach(skill => {
  const mdPath = path.join(skillsDir, skill, 'SKILL.md');
  if (!fs.existsSync(mdPath)) return;
  
  let content = fs.readFileSync(mdPath, 'utf8');
  if (!content.startsWith('---')) {
    // Add default frontmatter
    console.log(`Adding frontmatter to ${skill}`);
    content = `---\nname: ${skill}\nversion: 1.0.0\n---\n\n${content}`;
    fs.writeFileSync(mdPath, content);
  } else if (!content.includes('version:')) {
    // Inject version into existing frontmatter
    console.log(`Injecting version into ${skill}`);
    content = content.replace(/^---\n/, `---\nversion: 1.0.0\n`);
    fs.writeFileSync(mdPath, content);
  }
});
