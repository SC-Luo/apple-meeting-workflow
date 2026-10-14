# Opening shortcuts

Use native Shortcuts opening actions. The requested baseline needs no remote-login service, shell execution permission, or automatic microphone recording.

- **Glossary:** URL action with the user's Sheet link, followed by Open URLs. Works as an opening shortcut on Mac/iPhone with the corresponding Google account signed in.
- **Mac recording:** Open App → installed Anarlog. It opens the recorder; the user starts recording.
- **iPhone recording:** Open App → Voice Memos. It opens the phone's recorder; the user starts recording.

Build these through Shortcuts UI or use `scripts/build_shortcuts.py`. The builder creates unsigned definitions locally. Use Apple's `shortcuts sign --mode anyone` to make an importable file; Apple receives the shortcut for signing validation. Personalized links remain in the user's local output and are not included in this public repository.

Open App definitions require `WFSelectedApp` with `BundleIdentifier` and `Name`, in addition to `WFAppIdentifier`. Merely signing a definition with `WFAppIdentifier` can succeed while leaving the App parameter empty. Check the imported action and actually run it. App availability and action serialization can vary by version.

Do not produce duplicate shortcut names silently. Replace only a shortcut created for this workflow when authorized, or choose a distinct name. Preserve unrelated shortcuts. iCloud synchronization and iPhone installation must be checked on the user's phone; a Mac library entry alone is not proof of phone execution.

Use the user's desired launch surface, such as Siri, a widget, or Home Screen. For URL launch from another app, Apple's supported format is `shortcuts://run-shortcut?name=URL_ENCODED_NAME`.

Sources:

- https://support.apple.com/guide/shortcuts-mac/apd455c82f02/mac
- https://support.apple.com/guide/shortcuts/apd624386f42/ios
