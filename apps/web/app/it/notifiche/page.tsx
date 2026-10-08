import NotificationList from "./NotificationList";

export const metadata = { title: "Notifiche — PetMatch AI" };

export default function NotificationsPage() {
  return <main className="catalog-page"><a className="catalog-home" href="/">PetMatch AI</a><header className="catalog-heading"><p className="eyebrow">Il tuo account</p><h1>Notifiche di compatibilità.</h1><p className="intro">Nuovi animali che corrispondono al tuo profilo.</p></header><NotificationList /></main>;
}
