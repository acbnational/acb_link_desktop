# ACB Link Desktop - Future Roadmap

**Version:** 1.0  
**Last Updated:** January 2026  
**Developed by:** Blind Information Technology Solutions (BITS)  
**For:** American Council of the Blind (ACB)

---

## Overview

This document outlines future enhancements planned for ACB Link Desktop beyond the current version 1.0 release. For a complete list of implemented features, see [FEATURES.md](FEATURES.md).

All features in version 1.0 have been completed, including:

- Cross-platform support (Windows and macOS)
- WCAG 2.2 AA accessibility compliance
- VoiceOver deep integration for macOS
- GitHub-based automatic updates
- System-level scheduling (Windows Task Scheduler, macOS launchd)
- Live data synchronization from ACB servers
- **GitHub-based admin authentication** (zero infrastructure cost)
- Centralized configuration management with role-based access
- Affiliate correction workflow with admin review

---

## Completed Features (v1.0)

### Administration System ✓ (Implemented January 2025)

**GitHub-Based Authentication:**
- Zero infrastructure cost (uses GitHub as identity provider)
- Automatic role assignment from repository permissions
- Secure Personal Access Token authentication
- Session management with automatic expiry

**Role-Based Access Control:**
- SUPER_ADMIN: Full configuration access (organization owners)
- CONFIG_ADMIN: Settings management (repository admins)
- AFFILIATE_ADMIN: Affiliate data corrections (repository contributors)
- USER: Standard read-only access (all users)

**Affiliate Correction Workflow:**
- User-submitted corrections with documentation
- Admin review queue with approve/reject actions
- Audit trail for all administrative changes
- Real-time sync of approved corrections

---

## Future Enhancements

### Cloud Sync and Accounts (Planned: Q3 2025)

**Priority:** Medium  
**Complexity:** High

- ACB member login integration
- Cross-device sync of favorites and playlists
- Cloud playlist backup and restore
- Listening history and statistics
- Sync settings across devices

### AI-Powered Features (Planned: Q4 2025)

**Priority:** Medium  
**Complexity:** High

- Automatic podcast transcription
- Searchable transcript database
- Episode summarization
- Personalized content recommendations
- Smart content discovery based on listening patterns

### Linux Support (Planned: 2026)

**Priority:** Low  
**Complexity:** Medium

- Linux native application (GTK or Qt)
- Orca screen reader support
- Flatpak and Snap packaging
- Ubuntu, Debian, and Fedora packages

### Mobile Companion Apps (Planned: 2027)

**Priority:** Low  
**Complexity:** Very High

- iOS companion app
- Android companion app
- Remote control via mobile
- Push notifications on mobile
- Mobile-to-desktop sync

### Additional Languages (Ongoing)

**Priority:** Medium  
**Complexity:** Medium

- French translation
- German translation
- Portuguese translation
- Right-to-left language support (Arabic, Hebrew)

### Advanced Audio Features (Future)

**Priority:** Low  
**Complexity:** Medium

- Bluetooth device management
- Audio device selection per stream
- Surround sound support
- Audio effects and filters

### Social Features (Future)

**Priority:** Low  
**Complexity:** Medium

- Share favorite episodes
- Community playlists
- Listener chat during live events
- Episode comments and ratings

---

## Technical Improvements

### Code Quality

- Unit test coverage (target: 80%)
- Integration test suite
- CI/CD pipeline with automated testing
- Code coverage reporting
- Automated accessibility testing

### Performance Optimization

- Lazy module loading
- Memory usage optimization
- Startup time reduction
- Background task optimization

### Security Enhancements

- ✓ Secure credential storage (GitHub PAT in memory only)
- ✓ GitHub-based authentication for admin features
- Regular security audits
- Encrypted local storage option

---

## Infrastructure

### Distribution ✓ (Implemented January 2025)

- Microsoft Store submission support
- Mac App Store submission support
- Delta updates (patch-only downloads)

### Analytics (Privacy-Respecting) ✓ (Implemented January 2025)

- Opt-in usage statistics
- Crash reporting
- Feature usage tracking
- Performance monitoring

All analytics are:
- **Disabled by default** - requires explicit user consent
- **Privacy-first** - no personally identifiable information collected
- **Transparent** - users can view exactly what data is collected
- **User-controlled** - data can be cleared at any time

---

## Community Requests

This section will be updated based on user feedback and community requests.

Have a feature request? Contact us:

- **Email**: bits@acb.org
- **GitHub Issues**: [github.com/acbnational/acb_link_desktop/issues](https://github.com/acbnational/acb_link_desktop/issues)
- **Phone**: 1-800-424-8666

---

## Contributing

ACB Link Desktop is developed by BITS. We welcome contributions:

- **Bug Reports**: Help us find and fix issues
- **Feature Requests**: Suggest improvements
- **Code Contributions**: Submit pull requests
- **Translations**: Help localize the app
- **Testing**: Report accessibility issues

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

*Roadmap Version 1.0*  
*Last Updated: January 2026*  
*Copyright 2026 American Council of the Blind / BITS*
