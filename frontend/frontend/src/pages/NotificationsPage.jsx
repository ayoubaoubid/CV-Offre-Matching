import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../context/AuthContext";
import {
  getNotifications,
  markNotificationAsRead,
} from "../services/notificationService";


export default function NotificationsPage() {
  const { authReady, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authReady) {
      return;
    }
    if (!user) {
      navigate("/");
      return;
    }
    if (user.role === "admin") {
      navigate("/recruiter");
      return;
    }
    let isMounted = true;
    const loadInitialNotifications = async () => {
      try {
        const response = await getNotifications();
        if (isMounted) {
          setNotifications(Array.isArray(response.data) ? response.data : []);
          setError("");
        }
      } catch {
        if (isMounted) {
          setError("Impossible de charger les notifications.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadInitialNotifications();
    return () => {
      isMounted = false;
    };
  }, [authReady, navigate, user]);

  const readNotification = async (notificationId) => {
    await markNotificationAsRead(notificationId);
    setNotifications((current) =>
      current.map((notification) =>
        notification.id === notificationId
          ? { ...notification, is_read: true }
          : notification
      )
    );
  };

  if (!authReady) {
    return <div className="page-frame py-5"><p>Chargement...</p></div>;
  }

  return (
    <div className="app-page">
      <div className="page-frame">
        <section className="dashboard-hero mb-4">
          <div>
            <span className="section-tag">Notifications</span>
            <h2 className="mb-3">Messages de candidature</h2>
            <p className="text-muted mb-0">
              Retrouvez les reponses des recruteurs sur vos candidatures.
            </p>
          </div>
        </section>

        {error ? <p className="text-danger">{error}</p> : null}
        {loading ? <p>Chargement des notifications...</p> : null}

        <div className="d-grid gap-3">
          {notifications.map((notification) => (
            <article className="surface-card info-card" key={notification.id}>
              <div className="d-flex justify-content-between gap-3 flex-wrap">
                <div>
                  <span className={`badge ${notification.is_read ? "text-bg-light" : "text-bg-primary"} mb-2`}>
                    {notification.is_read ? "Lu" : "Nouveau"}
                  </span>
                  <h5 className="mb-2">{notification.title}</h5>
                  <p className="mb-2">{notification.message}</p>
                  {notification.job_title ? (
                    <p className="small text-muted mb-0">Offre : {notification.job_title}</p>
                  ) : null}
                </div>
                {!notification.is_read ? (
                  <button
                    className="btn btn-outline-primary btn-sm align-self-start"
                    onClick={() => readNotification(notification.id)}
                  >
                    Marquer comme lu
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>

        {!notifications.length && !loading ? (
          <div className="surface-card info-card">
            <p className="text-muted mb-0">Aucune notification pour le moment.</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
