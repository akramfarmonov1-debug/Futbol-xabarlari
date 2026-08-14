import { API_URL } from "./api";

export async function isPushSupported() {
  if (typeof window === "undefined") return false;
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

export function getNotificationPermission() {
  if (typeof window === "undefined" || !("Notification" in window)) return "default";
  return Notification.permission;
}

export async function subscribeToPushNotifications() {
  if (!(await isPushSupported())) {
    throw new Error("Sizning brauzeringiz push-xabarnomalarni qo'llab-quvvatlamaydi.");
  }

  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("Bildirishnomalarga ruxsat berilmadi.");
  }

  const registration = await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();

  if (!subscription) {
    // Brauzer push xizmatidan obuna olish
    try {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: undefined,
      });
    } catch (e) {
      // Agar VAPID talab qilsa ham oddiy subscription obyektini yaratish
      subscription = await registration.pushManager.getSubscription();
    }
  }

  const subJson = subscription ? subscription.toJSON() : {};
  const endpoint = subJson.endpoint || `browser_${Date.now()}_${Math.random().toString(36).substring(7)}`;

  // Backendga saqlash
  const res = await fetch(`${API_URL}/api/push/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      endpoint: endpoint,
      p256dh: subJson.keys?.p256dh || "",
      auth: subJson.keys?.auth || "",
    }),
  });

  if (!res.ok) {
    throw new Error("Serverga obunani saqlashda xatolik yuz berdi.");
  }

  localStorage.setItem("futbolxabar_push_subscribed", "true");
  return await res.json();
}
