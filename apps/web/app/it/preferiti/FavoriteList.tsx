"use client";

import { useEffect, useState } from "react";

type Favorite = { id: string; name: string; slug: string; species: string; size: string | null; shelter: { name: string; comune: { name: string } } };

export default function FavoriteList() {
  const [items, setItems] = useState<Favorite[]>([]);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    fetch("/api/matching/favorites", { cache: "no-store" }).then((response) => response.json()).then((data) => setItems(data.favorites ?? [])).finally(() => setLoaded(true));
  }, []);
  if (!loaded) return <p role="status">Caricamento dei preferiti…</p>;
  if (!items.length) return <section className="catalog-empty"><h2>Non hai ancora salvato preferiti</h2><p>Puoi aggiungerli dalla pagina dei risultati.</p><a className="button" href="/it/abbinamento">Crea il tuo profilo</a></section>;
  return <section className="animal-grid" aria-label="Animali preferiti">{items.map((animal) => <article className="animal-card" key={animal.id}><div className="animal-card-body"><p className="animal-meta">{animal.species === "dog" ? "Cane" : "Gatto"}{animal.size ? ` · ${animal.size}` : ""}</p><h2>{animal.name}</h2><p className="animal-shelter">{animal.shelter.name} · {animal.shelter.comune.name}</p><a className="match-catalog-link" href={`/it/animali?q=${encodeURIComponent(animal.name)}`}>Cerca nel catalogo</a><button className="button secondary" type="button" onClick={async () => { await fetch(`/api/matching/favorites?animalId=${encodeURIComponent(animal.id)}`, { method: "DELETE" }); setItems((current) => current.filter((item) => item.id !== animal.id)); }}>Rimuovi</button></div></article>)}</section>;
}
