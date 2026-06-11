# Posture Monitor Pro - Frontend

Modern Vue 3 + Vite frontend for real-time posture monitoring with privacy controls.

## Features

- ✅ Consent gate (mandatory before use) - EU-02, EU-05
- ✅ Age verification (COPPA) - NA-04
- ✅ Real-time WebSocket posture monitoring
- ✅ Privacy & Data Management center
- ✅ DSAR (Data Subject Access Requests) UI
- ✅ Data export & deletion interface
- ✅ Multi-language support (EN/FR)
- ✅ Modern, responsive design
- ✅ Local-first, no cookies or trackers

## Architecture

```
frontend/
├── package.json         # Node dependencies
├── vite.config.js       # Vite build config
├── index.html           # HTML entry point
├── src/
│   ├── main.js          # Vue app entry
│   ├── style.css        # Global styles
│   ├── App.vue          # Main app component
│   ├── components/      # Reusable components
│   │   ├── ConsentGate.vue    # Mandatory consent screen
│   │   └── AgeGate.vue        # Age verification
│   ├── pages/           # Page components
│   │   ├── Dashboard.vue      # Stats & history
│   │   ├── PostureMonitor.vue # Live monitoring
│   │   └── PrivacyCenter.vue  # DSAR & data management
│   └── stores/          # Pinia state management
│       └── userStore.js       # User & auth state
```

## Key Pages

### Consent Gate
- Mandatory before access
- Privacy policy display
- Language selector
- Compliance badges

### Age Gate
- COPPA compliance (13+)
- Date picker for verification
- Blocks minors from use

### Dashboard
- Real-time posture statistics
- Historical data visualization
- Alert tracking
- Session summaries

### Posture Monitor
- Live WebSocket stream
- Real-time metrics
- Sensitivity controls
- Sound/visual alerts

### Privacy Center
- **Export Data** - GDPR Article 20 (Right to Portability)
- **Delete Data** - GDPR Article 17 (Right to Erasure)
- **DSAR Request** - Comprehensive data access
- **Consent Management** - Withdraw or update consent

## Running

From project root:

```bash
# Both backend and frontend
python launch.py

# Frontend only (requires backend running)
python launch.py --frontend-only

# Or manually
cd frontend
npm install      # First time only
npm run dev      # Starts dev server at http://localhost:5173
npm run build    # Production build
```

## Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Compliance Features

### EU-02 (RGPD - Legal Basis)
- Mandatory consent screen before any data collection
- Clear disclosure of data uses
- Multi-language privacy notices

### EU-04 (RGPD - User Rights)
- Data export button (Right to Portability)
- Data deletion button (Right to Erasure)
- Audit log access
- DSAR request interface

### EU-05 (ePrivacy)
- No cookies or trackers
- LocalStorage only for user session
- No third-party integrations

### NA-03 (BIPA)
- Explicit consent required for biometric processing
- Clear disclosure: "Images processed in-memory, never stored"
- Data retention timeline

### NA-04 (COPPA)
- Age gate before registration (13+ required)
- Parental consent path (implemented server-side)

## API Integration

Frontend communicates with backend via:

- **REST API** (`/api/*`) - Data access, DSAR, settings
- **WebSocket** (`/ws/posture/*`) - Real-time posture streaming

All requests include user ID from localStorage.

## State Management (Pinia)

`userStore` manages:
- User ID & authentication
- Consent status
- Age verification
- Language preference
- API instance with auth headers

## Styling

- Global variables in `src/style.css`
- Component-scoped styles in `.vue` files
- Responsive grid layouts
- Accessible color contrast
- Print-friendly layouts

## Security Notes

- No sensitive data in LocalStorage (only user ID & settings)
- No API keys or passwords stored
- CORS restricted to localhost
- All API calls over HTTP (local-only)

## Production Considerations

Before deploying to production:

1. **Build optimization**
   ```bash
   npm run build
   # Outputs to dist/ - serve with HTTP/2 + gzip
   ```

2. **HTTPS**
   - Use HTTPS in production
   - Set secure cookies if adding auth

3. **CSP Headers**
   - Implement Content Security Policy
   - Restrict inline scripts

4. **Backend API**
   - Change from `127.0.0.1:8000` to production domain
   - Implement rate limiting
   - Add API authentication if needed

5. **Monitoring**
   - Add error tracking (Sentry, etc.)
   - Log user interactions
   - Monitor performance metrics

## Compliance Checklist

See `reglementation.md` for full tracking.

Key items for frontend:
- [x] ConsentGate component (EU-02)
- [x] AgeGate component (NA-04)
- [x] PrivacyCenter - export functionality (EU-04)
- [x] PrivacyCenter - delete functionality (EU-04)
- [x] DSAR request interface (EU-04)
- [x] Privacy policy display (EU-04)
- [ ] Language localization (i18n)
- [ ] Accessibility audit (WCAG 2.1)
