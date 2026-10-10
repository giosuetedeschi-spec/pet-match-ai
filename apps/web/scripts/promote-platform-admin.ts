import { prisma } from "../lib/prisma";

const email = process.env.ADMIN_EMAIL?.trim().toLowerCase();
if (!email) throw new Error("Set ADMIN_EMAIL to the verified account that should become platform_admin.");
const result = await prisma.user.updateMany({
  where: { email, emailVerifiedAt: { not: null }, status: "active", deletedAt: null },
  data: { role: "platform_admin" },
});
await prisma.$disconnect();
if (result.count !== 1) throw new Error("No verified active account was promoted. Verify ADMIN_EMAIL and the account state.");
console.info(`Promoted ${email} to platform_admin.`);
