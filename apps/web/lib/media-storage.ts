import { GetObjectCommand, PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";

const bucket = process.env.MEDIA_S3_BUCKET?.trim();
const region = process.env.MEDIA_S3_REGION || "eu-south-1";
const endpoint = process.env.MEDIA_S3_ENDPOINT?.trim();
const localRoot = path.resolve(/*turbopackIgnore: true*/ process.env.MEDIA_LOCAL_PATH || path.join(process.cwd(), ".media"));
const s3 = bucket
  ? new S3Client({
      region,
      ...(endpoint ? { endpoint, forcePathStyle: true } : {}),
      ...(process.env.MEDIA_S3_ACCESS_KEY_ID && process.env.MEDIA_S3_SECRET_ACCESS_KEY
        ? { credentials: { accessKeyId: process.env.MEDIA_S3_ACCESS_KEY_ID, secretAccessKey: process.env.MEDIA_S3_SECRET_ACCESS_KEY } }
        : {}),
    })
  : null;

function localPath(key: string) {
  const resolved = path.resolve(localRoot, ...key.split("/"));
  if (!resolved.startsWith(`${localRoot}${path.sep}`)) throw new Error("Invalid media key.");
  return resolved;
}

export async function saveMedia(key: string, body: Buffer, contentType = "image/webp") {
  if (bucket && s3) {
    await s3.send(new PutObjectCommand({ Bucket: bucket, Key: key, Body: body, ContentType: contentType }));
    return;
  }
  const destination = localPath(key);
  await mkdir(path.dirname(destination), { recursive: true });
  const temporary = `${destination}.${crypto.randomUUID()}.tmp`;
  await writeFile(temporary, body, { flag: "wx" });
  await rename(temporary, destination);
}

export async function readMedia(key: string) {
  if (bucket && s3) {
    const object = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    if (!object.Body) throw new Error("Media object has no body.");
    return Buffer.from(await object.Body.transformToByteArray());
  }
  return readFile(localPath(key));
}

