# Security Policy

## 🔒 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

---

## 🚨 Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in ZeroTouch Atlas, please report it responsibly.

### **DO NOT** Open a Public GitHub Issue

Public disclosure of security vulnerabilities puts all users at risk. Instead, use one of the following methods:

---

## Reporting Methods

### Method 1: GitHub Security Advisories (Preferred)

1. Navigate to the [Security tab](https://github.com/jevenson76/Atlas-Orchestrator/security)
2. Click "Report a vulnerability"
3. Fill in the advisory form with details

### Method 2: Direct Email

Email the project maintainer directly at:
- **Email**: [Create and add your secure email here]
- **Subject**: `[SECURITY] ZeroTouch Atlas Vulnerability Report`

### Method 3: Encrypted Communication

For highly sensitive issues, use PGP encryption:
- **PGP Key**: [Add PGP public key fingerprint if desired]

---

## What to Include in Your Report

Please provide the following information:

1. **Vulnerability Description**
   - What is the security issue?
   - What component/file is affected?

2. **Attack Scenario**
   - How could this be exploited?
   - What is the potential impact?

3. **Reproduction Steps**
   - Step-by-step instructions to reproduce the issue
   - Include code snippets, configurations, or commands if applicable

4. **Environment Details**
   - ZeroTouch Atlas version
   - Operating system
   - Python version
   - Any relevant configuration

5. **Suggested Fix** (Optional)
   - If you have ideas for remediation, please share them
   - Pull requests for security fixes are welcome (after coordinated disclosure)

---

## Our Commitment to You

### Response Time

- **Initial Response**: Within **48 hours**
- **Severity Assessment**: Within **7 days**
- **Fix Timeline**:
  - **Critical**: 7 days
  - **High**: 30 days
  - **Medium**: 60 days
  - **Low**: 90 days

### What You Can Expect

1. ✅ Acknowledgment of your report
2. ✅ Regular updates on fix progress
3. ✅ Credit in security advisory (if you wish)
4. ✅ Notification when fix is released
5. ✅ Coordinated public disclosure

---

## Coordinated Disclosure Process

We follow **responsible disclosure** practices:

1. **Report Received**: We acknowledge receipt within 48 hours
2. **Verification**: We verify and assess severity (7 days)
3. **Fix Development**: We develop and test the fix
4. **Private Notification**: We notify you of the fix
5. **Public Release**: Fix is released with security advisory
6. **Coordinated Disclosure**: 90 days after initial report (or sooner if agreed)

### Disclosure Timeline

- **Day 0**: Vulnerability reported
- **Day 2**: Acknowledgment sent
- **Day 7**: Severity confirmed, fix in progress
- **Day 7-90**: Fix developed, tested, and released
- **Day 90**: Public disclosure (if not already resolved)

---

## Security Best Practices for Users

### 1. **API Key Management**

✅ **DO**:
- Store API keys in `.env` files (NOT committed to git)
- Use environment variables for all secrets
- Rotate keys regularly (every 90 days)
- Use separate keys for dev/staging/production

❌ **DON'T**:
- Commit API keys to git
- Hardcode secrets in source code
- Share keys via email/chat
- Use production keys in development

### 2. **Network Security**

✅ **DO**:
- Keep Atlas on localhost by default (`127.0.0.1:8501`)
- Use HTTPS/SSL if exposing to network
- Implement authentication if multi-user
- Use firewall rules to restrict access

❌ **DON'T**:
- Expose Streamlit app to public internet without auth
- Use `--server.address 0.0.0.0` in production without security
- Disable security filter in production

### 3. **Dependency Updates**

✅ **DO**:
- Run `pip list --outdated` regularly
- Update dependencies monthly
- Review security advisories
- Use `pip install --upgrade` for critical updates

❌ **DON'T**:
- Ignore dependency update warnings
- Run outdated packages with known vulnerabilities

### 4. **Input Validation**

✅ **DO**:
- Keep Zero-Trust security filter enabled
- Validate all user inputs
- Sanitize file uploads
- Use rate limiting

❌ **DON'T**:
- Disable input validation
- Trust user input without filtering
- Skip security checks for "trusted" users

---

## Known Security Considerations

### Current Security Posture

ZeroTouch Atlas implements the following security measures:

1. **Zero-Trust Input Boundary**: All inputs validated before execution
2. **API Key Security**: No secrets in code, environment variables only
3. **Rate Limiting**: 30 requests/min, 500 requests/hour
4. **Input Sanitization**: Prompt injection, SQL injection, XSS prevention
5. **Sandboxed Execution**: Dropzone files isolated to `~/dropzone/`

### Single-User Application

⚠️ **Important**: ZeroTouch Atlas is designed as a **single-user application**.

If deploying for multiple users:
- Implement authentication (OAuth, JWT, or basic auth)
- Add user isolation/sandboxing
- Implement per-user rate limiting
- Add audit logging

---

## Security Updates

Security updates are released as:
- **Patch versions** (2.0.1, 2.0.2) for minor security fixes
- **Minor versions** (2.1.0) for security enhancements
- **Major versions** (3.0.0) for security architecture changes

**Subscribe to security advisories**: Watch this repository and enable notifications for security alerts.

---

## Scope

### In Scope

The following are within the scope of our security policy:

✅ **Code Vulnerabilities**:
- Prompt injection
- SQL injection
- XSS (Cross-site scripting)
- Command injection
- Path traversal
- Authentication bypass
- Authorization issues

✅ **Dependency Vulnerabilities**:
- Known CVEs in dependencies
- Outdated packages with security issues

✅ **Configuration Issues**:
- Insecure defaults
- Exposed secrets
- Weak encryption

### Out of Scope

The following are **out of scope**:

❌ **User Misconfigurations**:
- Exposing app to internet without auth
- Committing API keys to git
- Using weak passwords

❌ **Physical Access**:
- Local machine compromise
- Stolen credentials

❌ **Social Engineering**:
- Phishing attacks on users
- Social manipulation

❌ **Third-Party Services**:
- Anthropic/OpenAI/Google API vulnerabilities
- Cloud provider issues

---

## Hall of Fame

We recognize and thank security researchers who responsibly disclose vulnerabilities:

| Researcher | Vulnerability | Severity | Date |
|------------|---------------|----------|------|
| *(None yet)* | - | - | - |

**Want to be listed?** Report a valid security issue and we'll credit you here (with your permission).

---

## Contact

For security-related questions (not vulnerability reports):
- **GitHub Discussions**: [Security Category](https://github.com/jevenson76/Atlas-Orchestrator/discussions)
- **General Security Inquiries**: Open a discussion tagged `security`

For **vulnerability reports**, use the methods listed at the top of this document.

---

## License

This security policy is part of the ZeroTouch Atlas project.

---

**Last Updated**: November 7, 2025
**Policy Version**: 1.0
**Next Review**: February 7, 2026 (every 90 days)
