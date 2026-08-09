import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import {
  AccessToken,
  type AccessTokenOptions,
  type VideoGrant,
} from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const AGENT_NAME = process.env.AGENT_NAME;

export const revalidate = 0;

export async function POST(req: Request) {
  try {
    if (!LIVEKIT_URL) {
      throw new Error('LIVEKIT_URL is not defined');
    }

    if (!API_KEY) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }

    if (!API_SECRET) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    const body = await req.json().catch(() => ({}));

    let roomConfig: RoomConfiguration | undefined;

    if (body?.room_config) {
      roomConfig = RoomConfiguration.fromJson(body.room_config, {
        ignoreUnknownFields: true,
      });
    } else if (AGENT_NAME) {
      roomConfig = RoomConfiguration.fromJson(
        {
          agents: [{ agentName: AGENT_NAME }],
        },
        {
          ignoreUnknownFields: true,
        },
      );
    }

    // Persistent Medha user ID
    const cookieStore = await cookies();

    let userId = cookieStore.get('medha_user_id')?.value;

    if (!userId) {
      userId = `medha_user_${crypto.randomUUID()}`;
    }

    console.log('MEDHA USER ID:', userId);

    const participantName = 'user';
    const participantIdentity = userId;

    const roomName = `voice_assistant_room_${Math.floor(
      Math.random() * 10000,
    )}`;

    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName,
      },
      roomName,
      roomConfig,
    );

    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName,
      participantToken,
    };

    const headers = new Headers({
      'Cache-Control': 'no-store',
    });

    if (!cookieStore.get('medha_user_id')) {
      headers.append(
        'Set-Cookie',
        `medha_user_id=${userId}; Path=/; Max-Age=31536000; SameSite=Lax`,
      );
    }

    return NextResponse.json(data, { headers });
  } catch (error) {
    console.error(error);

    if (error instanceof Error) {
      return new NextResponse(error.message, {
        status: 500,
      });
    }

    return new NextResponse('Unknown error', {
      status: 500,
    });
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  roomConfig?: RoomConfiguration,
): Promise<string> {
  const at = new AccessToken(API_KEY!, API_SECRET!, {
    ...userInfo,
    ttl: '15m',
  });

  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };

  at.addGrant(grant);

  if (roomConfig) {
    at.roomConfig = roomConfig;
  }

  return at.toJwt();
}