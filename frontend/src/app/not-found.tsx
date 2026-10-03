import Link from "next/link";

export default function NotFound() {
  return (
    <div className="page-shell simple-page empty-state">
      <p className="eyebrow">404</p>
      <h1>We could not find that ingredient.</h1>
      <Link className="button" href="/">Back to catalogue</Link>
    </div>
  );
}
