import { FunctionDeclaration, SchemaType } from '@google/generative-ai';

// ─── Tool declarations (sent to Gemini so it knows what tools exist) ──────────

export const toolDeclarations: FunctionDeclaration[] = [
  {
    name: 'search_web',
    description:
      'Search the internet for current information on any topic, news, prices, schedules, event details, etc.',
    parameters: {
      type: SchemaType.OBJECT,
      properties: {
        query: {
          type: SchemaType.STRING,
          description: 'The search query string',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'search_youtube',
    description:
      'Search YouTube for video tutorials, lectures, or content on a specific topic',
    parameters: {
      type: SchemaType.OBJECT,
      properties: {
        query: {
          type: SchemaType.STRING,
          description: 'YouTube search query',
        },
        max_results: {
          type: SchemaType.NUMBER,
          description: 'Maximum number of results to return (default: 5)',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'find_courses',
    description:
      'Find free online courses, tutorials, and certifications on platforms like Coursera, edX, freeCodeCamp, Khan Academy, YouTube',
    parameters: {
      type: SchemaType.OBJECT,
      properties: {
        topic: {
          type: SchemaType.STRING,
          description: 'The subject or skill to learn',
        },
        level: {
          type: SchemaType.STRING,
          description: 'Skill level: beginner, intermediate, or advanced',
        },
      },
      required: ['topic'],
    },
  },
  {
    name: 'compare_platforms',
    description:
      'Compare different platforms, apps, or services and recommend the best one for a given purpose',
    parameters: {
      type: SchemaType.OBJECT,
      properties: {
        purpose: {
          type: SchemaType.STRING,
          description: 'What the user wants to do or achieve',
        },
      },
      required: ['purpose'],
    },
  },
];

// ─── Tool implementations ─────────────────────────────────────────────────────

/** Web search via Tavily (with DuckDuckGo fallback) */
export async function searchWeb(
  query: string,
  tavilyKey?: string | null
): Promise<string> {
  // ── Tavily (best quality) ──
  if (tavilyKey) {
    try {
      const res = await fetch('https://api.tavily.com/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: tavilyKey,
          query,
          search_depth: 'basic',
          max_results: 5,
        }),
      });
      const data = await res.json();
      if (data.results?.length) {
        const formatted = (data.results as any[])
          .map(
            (r, i) =>
              `${i + 1}. ${r.title}\n${r.content?.slice(0, 250) ?? ''}\nURL: ${r.url}`
          )
          .join('\n\n');
        return `Search results for "${query}":\n\n${formatted}`;
      }
    } catch (err) {
      console.warn('[agentTools] Tavily error:', err);
    }
  }

  // ── DuckDuckGo Instant Answer (free, no key) ──
  try {
    const res = await fetch(
      `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_redirect=1&no_html=1&skip_disambig=1`
    );
    const data = await res.json();

    let result = '';
    if (data.AbstractText) result += data.AbstractText + '\n';
    if (data.Answer) result += `Answer: ${data.Answer}\n`;
    if (data.RelatedTopics?.length) {
      const topics = (data.RelatedTopics as any[])
        .slice(0, 4)
        .filter((t) => t.Text)
        .map((t) => `• ${t.Text}`)
        .join('\n');
      if (topics) result += `\nRelated:\n${topics}`;
    }

    if (result.trim()) return result.trim();
    return (
      `No instant answer found for "${query}". ` +
      `For full web results, add a free Tavily API key (app.tavily.com).`
    );
  } catch (err) {
    return `Web search temporarily unavailable: ${String(err)}`;
  }
}

/** YouTube search via Invidious (free, no API key needed) */
export async function searchYouTube(
  query: string,
  maxResults: number = 5
): Promise<string> {
  const instances = [
    'https://invidious.kavin.rocks',
    'https://vid.puffyan.us',
    'https://invidious.snopyta.org',
  ];

  for (const instance of instances) {
    try {
      const res = await fetch(
        `${instance}/api/v1/search?q=${encodeURIComponent(query)}&type=video` +
          `&fields=videoId,title,author,viewCountText,lengthSeconds&page=1`
      );
      if (!res.ok) continue;
      const videos = await res.json();
      if (!Array.isArray(videos) || videos.length === 0) continue;

      const lines = (videos as any[]).slice(0, maxResults).map((v, i) => {
        const mins = Math.floor((v.lengthSeconds || 0) / 60);
        const secs = String((v.lengthSeconds || 0) % 60).padStart(2, '0');
        return (
          `${i + 1}. "${v.title}" — ${v.author}\n` +
          `   ⏱ ${mins}:${secs}  👁 ${v.viewCountText || 'N/A'}\n` +
          `   🔗 https://youtube.com/watch?v=${v.videoId}`
        );
      });
      return `YouTube results for "${query}":\n\n${lines.join('\n\n')}`;
    } catch {
      continue;
    }
  }

  return (
    `YouTube search is currently unavailable via the API. ` +
    `Try: https://youtube.com/results?search_query=${encodeURIComponent(query)}`
  );
}

/** Return structured free course recommendations for a topic */
export async function findCourses(
  topic: string,
  level?: string
): Promise<string> {
  const lvl = level ? ` (${level} level)` : '';
  const enc = encodeURIComponent(topic);
  return (
    `Free courses & certifications for "${topic}"${lvl}:\n\n` +
    `🎓 Coursera – coursera.org/search?query=${enc}\n` +
    `   Audit for free | Certificates from Google, Meta, Stanford\n\n` +
    `📘 edX – edx.org/search#q=${enc}\n` +
    `   Free audit | MIT, Harvard, Microsoft courses\n\n` +
    `💻 freeCodeCamp – freecodecamp.org\n` +
    `   100% free + certificates | Web dev, Python, Data Science\n\n` +
    `🎯 Khan Academy – khanacademy.org\n` +
    `   Completely free | Math, Science, Programming basics\n\n` +
    `📺 YouTube – youtube.com/results?search_query=${enc}+tutorial\n` +
    `   Free videos | Traversy Media, CS50, freeCodeCamp channel\n\n` +
    `🏆 Google Skillshop – skillshop.google.com\n` +
    `   Free Google certs | Ads, Analytics, Cloud\n\n` +
    `☁️ AWS Skill Builder – explore.skillbuilder.aws\n` +
    `   Free cloud training & certifications\n\n` +
    `🔷 Microsoft Learn – learn.microsoft.com\n` +
    `   Free Azure, AI, Power BI certifications`
  );
}

/** Compare platforms for a given purpose */
export async function comparePlatforms(purpose: string): Promise<string> {
  return `I'll compare the best platforms for: "${purpose}". Searching for up-to-date recommendations...`;
}

// ─── Dispatcher ───────────────────────────────────────────────────────────────

export async function executeTool(
  toolName: string,
  args: Record<string, any>,
  tavilyKey?: string | null
): Promise<string> {
  switch (toolName) {
    case 'search_web':
      return searchWeb(args.query as string, tavilyKey);
    case 'search_youtube':
      return searchYouTube(args.query as string, args.max_results as number | undefined);
    case 'find_courses':
      return findCourses(args.topic as string, args.level as string | undefined);
    case 'compare_platforms':
      return comparePlatforms(args.purpose as string);
    default:
      return `Unknown tool: ${toolName}`;
  }
}
