function clampSuggestionCount(rawCount: unknown) {
  if (typeof rawCount !== "number" || !Number.isFinite(rawCount)) {
    return 3;
  }
  return Math.max(1, Math.min(5, Math.trunc(rawCount)));
}

export async function POST(request: Request) {
  const payload = await request
    .json()
    .catch(() => ({ n: 3 })) as { n?: unknown };

  return Response.json(
    {
      suggestions: [] as string[],
      count: clampSuggestionCount(payload.n),
    },
    {
      status: 200,
      headers: {
        "Cache-Control": "no-store",
      },
    },
  );
}
