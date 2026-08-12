import { NextResponse } from 'next/server';
import { execSync } from 'child_process';
import path from 'path';

const BACKEND_DIR = path.resolve(process.cwd(), '..', 'backend');

export const revalidate = 0;

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const userId = searchParams.get('user_id');
    const status = searchParams.get('status');

    let pyScript = `import json; from memory import get_escalations; print(json.dumps(get_escalations(`;
    if (userId) pyScript += `user_id="${userId}",`;
    if (status) pyScript += `status="${status}",`;
    pyScript += `)))`;

    const command = `uv run python -c "${pyScript}"`;
    const output = execSync(command, {
      cwd: BACKEND_DIR,
      encoding: 'utf-8',
    });

    const escalations = JSON.parse(output.trim());
    return NextResponse.json({ success: true, escalations });
  } catch (error) {
    console.error('Error fetching escalations:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch escalations' },
      { status: 500 }
    );
  }
}

export async function PATCH(req: Request) {
  try {
    const body = await req.json();
    const { ref_id, status } = body;

    if (!ref_id || !status) {
      return NextResponse.json(
        { success: false, error: 'Missing ref_id or status' },
        { status: 400 }
      );
    }

    const pyScript = `from memory import update_escalation_status; print(update_escalation_status("${ref_id}", "${status}"))`;
    const command = `uv run python -c "${pyScript}"`;

    execSync(command, {
      cwd: BACKEND_DIR,
      encoding: 'utf-8',
    });

    return NextResponse.json({ success: true, ref_id, status });
  } catch (error) {
    console.error('Error updating escalation status:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to update escalation status' },
      { status: 500 }
    );
  }
}
