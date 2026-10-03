export function Footer() {
  return (
    <footer className="site-footer">
      <img
        className="footer-hops-logo"
        src="/img/background/image-footer.svg"
        alt="Hop &amp; Barley hops illustration"
        width="484"
        height="264"
      />
      <nav className="footer-nav" aria-label="Footer navigation">
        <ul>
          <li><a href="#">Contact</a></li>
          <li><a href="#">FAQ</a></li>
          <li><a href="#">Community</a></li>
          <li><a href="#">Resources</a></li>
          <li><a href="#">License</a></li>
        </ul>
      </nav>
      <p className="footer-copyright">
        © Hop &amp; Barley {new Date().getFullYear()}. All rights reserved
      </p>
    </footer>
  );
}
