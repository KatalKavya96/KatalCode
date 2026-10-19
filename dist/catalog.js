"use strict";

// Keep this index aligned with completed editorials in the repository.
window.KATALCODE_CATALOG = {
  leetcode: {
    name: "LeetCode",
    initials: "LC",
    archiveUrl: "https://leetcode.com/contest/",
    description: "Weekly and biweekly contests with visual explanations and tested solutions.",
    contests: [
      {
        id: "weekly-524",
        title: "Weekly Contest 524",
        type: "Weekly",
        date: "October 18, 2026",
        summary: "Simulation and tree orientation: two questions explained from first thought to optimized solution.",
        problems: [
          {
            id: "q2-last-visited-cell",
            number: "Q2",
            platformId: "4084",
            title: "Last Visited Cell in a Directional Grid",
            difficulty: "Medium",
            pattern: "Simulation · Matrix",
            summary: "Follow the arrows and stop before leaving the grid or revisiting a cell.",
            storyTitle: "The maze that remembers",
            intro: "The path is deterministic. The only question is whether the next cell has already been visited.",
            panels: [
              ["First thought", "Follow the arrows", "A direct simulation mirrors the problem statement."],
              ["Bottleneck", "Remember where you have been", "Scanning a list of visited cells can make the walk quadratic."],
              ["Optimization", "Use a visited matrix", "Each lookup becomes constant time, and each cell is entered at most once."],
            ],
            insight: "Keep the simulation. Replace the expensive visited lookup.",
            takeaways: ["Time: O(mn), because each cell is visited at most once.", "Space: O(mn) for the visited matrix.", "Check the proposed move before entering the next cell."],
            simulator: "grid",
            source: "contests/leetcode/weekly/524/Q2-last-visited-cell/README.md",
          },
          {
            id: "q3-colored-tree-root",
            number: "Q3",
            platformId: "4085",
            title: "Find Root of a Colored Tree",
            difficulty: "Medium",
            pattern: "Trees · Edge orientation",
            summary: "Use the repeating color cycle to orient edges and identify the only possible root.",
            storyTitle: "The root with no incoming arrow",
            intro: "Trying every root works for small trees. But the colors already force the direction of every edge.",
            panels: [
              ["First thought", "Try every root", "Run BFS from each node and check the color and child rules."],
              ["Bottleneck", "Repeated traversals", "Up to n BFS runs cost O(n²) in the worst case."],
              ["Optimization", "Orient each edge once", "A valid root has indegree zero; every other node has indegree one."],
            ],
            insight: "A local color rule fixes all parent-child directions before any root is chosen.",
            takeaways: ["Time: O(n) to orient and inspect the edges.", "The unique root has indegree 0; every other node has indegree 1.", "The root must have degree at most 2; non-roots already have one parent."],
            simulator: "tree",
            source: "contests/leetcode/weekly/524/Q3-colored-tree-root/README.md",
          },
        ],
      },
    ],
  },
  codeforces: {
    name: "Codeforces",
    initials: "CF",
    archiveUrl: "https://codeforces.com/contests",
    description: "Contest solutions will appear here as they are documented.",
    contests: [],
  },
  codechef: {
    name: "CodeChef",
    initials: "CC",
    archiveUrl: "https://www.codechef.com/contests",
    description: "Contest solutions will appear here as they are documented.",
    contests: [],
  },
};
