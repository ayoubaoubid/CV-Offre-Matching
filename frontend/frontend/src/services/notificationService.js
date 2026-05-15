import API from "./api";


export async function getNotifications() {
  return API.get("/matching/notifications/");
}


export async function markNotificationAsRead(notificationId) {
  return API.patch(`/matching/notifications/${notificationId}/read/`);
}
