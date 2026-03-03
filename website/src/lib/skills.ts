import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

export interface SkillManifest {
    id: string;
    name: string;
    version: string;
    description: string;
    author?: string;
}

export async function getSkillsMap(): Promise<SkillManifest[]> {
    try {
        const skillsDir = path.join(process.cwd(), '..', 'skills');
        if (!fs.existsSync(skillsDir)) return [];

        const skillFolders = fs.readdirSync(skillsDir, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory() && !dirent.name.startsWith('.'))
            .map(dirent => dirent.name);

        const skills: SkillManifest[] = [];

        for (const folder of skillFolders) {
            const mdPath = path.join(skillsDir, folder, 'SKILL.md');
            if (!fs.existsSync(mdPath)) continue;

            try {
                const content = fs.readFileSync(mdPath, 'utf8');
                let name = folder;
                let version = '1.0.0';
                let description = 'A core OpenPango skill.';

                // Parse frontmatter explicitly
                const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
                if (frontmatterMatch) {
                    try {
                        const meta = yaml.load(frontmatterMatch[1]) as Record<string, any>;
                        if (meta.name) name = meta.name;
                        if (meta.version) version = String(meta.version);
                        if (meta.description) description = meta.description;
                    } catch (e) {
                        console.warn(`Failed to parse YAML for ${folder}`);
                    }
                }

                // Try to extract a description from the first H1 or paragraph if not in YAML
                const lines = content.split('\n');
                const titleLine = lines.find(l => l.startsWith('# '));
                if (titleLine && name === folder) {
                    // We can use the H1 as a fallback description if it's descriptive
                }

                skills.push({
                    id: folder,
                    name,
                    version,
                    description,
                });
            } catch (err) {
                console.error(`Error reading ${folder}/SKILL.md`, err);
            }
        }

        // Sort alphabetically
        return skills.sort((a, b) => a.id.localeCompare(b.id));

    } catch (error) {
        console.error("Failed to load skills map:", error);
        return [];
    }
}
