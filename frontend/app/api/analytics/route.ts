import { NextResponse } from 'next/server';
import { execSync } from 'child_process';
import path from 'path';

const BACKEND_DIR = path.resolve(process.cwd(), '..', 'backend');

export const revalidate = 0;

export async function GET() {
  try {
    const pyScript = `import json; from memory import get_call_analytics; print(json.dumps(get_call_analytics()))`;
    const command = `uv run python -c "${pyScript}"`;

    const output = execSync(command, {
      cwd: BACKEND_DIR,
      encoding: 'utf-8',
    });

    const analytics = JSON.parse(output.trim());
    return NextResponse.json({ success: true, analytics });
  } catch (error) {
    console.error('Error fetching analytics:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch analytics' },
      { status: 500 }
    );
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const {
      call_id,
      room_name,
      user_id,
      channel,
      duration_seconds,
      outcome,
      failure_reason,
      topic,
      exercises_completed,
      concept_lookups,
      first_response_latency_ms,
      caller_name,
    } = body;

    const callId = call_id || `sim_call_${Date.now()}`;
    const roomName = room_name || 'sim_room';
    const userId = user_id || 'test_student';
    const ch = channel || 'browser';
    const dur = duration_seconds ?? 30;
    const out = outcome || 'success';
    const top = topic || 'General Practice';
    const ex = exercises_completed ?? (out === 'success' ? 1 : 0);
    const cl = concept_lookups ?? (out === 'success' ? 1 : 0);
    const lat = first_response_latency_ms ?? 980;
    const name = caller_name || 'Test Caller';
    const failReason = failure_reason ? `"${failure_reason}"` : 'None';

    const pyScript = `import json; from memory import save_call_log; print(json.dumps(save_call_log(call_id="${callId}", room_name="${roomName}", user_id="${userId}", channel="${ch}", duration_seconds=${dur}, outcome="${out}", failure_reason=${failReason}, topic="${top}", exercises_completed=${ex}, concept_lookups=${cl}, first_response_latency_ms=${lat}, caller_name="${name}")))`;

    const command = `uv run python -c "${pyScript}"`;

    const output = execSync(command, {
      cwd: BACKEND_DIR,
      encoding: 'utf-8',
    });

    const result = JSON.parse(output.trim());
    return NextResponse.json({ success: true, call_log: result });
  } catch (error) {
    console.error('Error logging test call:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to record call log' },
      { status: 500 }
    );
  }
}
