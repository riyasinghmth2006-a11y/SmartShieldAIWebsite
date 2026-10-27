
    def _ensure_loaded(self) -> None:
        """Load only local artifacts; never download a large model at runtime."""
        if self._load_attempted:
            return

        self._load_attempted = True

        model_path = self.models_dir / "fake_news_model.joblib"
        vectorizer_path = self.models_dir / "fake_news_vectorizer.joblib"

        if not model_path.is_file() or not vectorizer_path.is_file():
            logger.warning(
                "Fake-news model artifacts are missing. "
                "Skipping model loading to avoid timeouts."
            )
            return

        try:
            import joblib

            self._legacy_model = joblib.load(model_path)
            self._legacy_vectorizer = joblib.load(vectorizer_path)

            logger.info("Local fake-news model loaded successfully.")

        except Exception:
            logger.exception("Could not load local fake-news model.")
            self._legacy_model = None
            self._legacy_vectorizer = None
