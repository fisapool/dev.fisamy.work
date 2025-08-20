# 🚀 Quick Setup Guide for Coder Templates

## ⚡ **Fast Setup (Copy & Paste)**

```bash
# 1. Navigate to the scripts directory
cd back-end/scripts

# 2. Set environment variables
export CODER_API_TOKEN="your_coder_api_token_here"
export CODER_HOST="https://coder.fisamy.work"

# 3. Run the setup script
./setup_coder_templates.sh
```

## 🔍 **What This Does**

The setup script will:
1. ✅ Check Python dependencies
2. ✅ Validate environment variables
3. ✅ Present a menu with 6 options:
   - Show template specifications
   - Show manual creation steps
   - Check existing templates
   - Test workspace functionality
   - Run full validation
   - Exit

## ⚠️ **Common Mistakes to Avoid**

### ❌ **Wrong Directory**
```bash
cd back-end
./scripts/setup_coder_templates.sh  # This will FAIL
```

### ❌ **Missing Environment Variables**
```bash
cd back-end/scripts
./setup_coder_templates.sh  # This will FAIL - no CODER_API_TOKEN
```

### ❌ **Wrong Variable Name**
```bash
export CODER_URL="..."  # Wrong! Use CODER_HOST
```

## ✅ **Correct Way (Step by Step)**

1. **Start from project root:**
   ```bash
   cd /path/to/your/project
   ```

2. **Navigate to scripts:**
   ```bash
   cd back-end/scripts
   ```

3. **Set your token:**
   ```bash
   export CODER_API_TOKEN="your_coder_api_token_here"
   ```

4. **Set the host:**
   ```bash
   export CODER_HOST="https://coder.fisamy.work"
   ```

5. **Run the script:**
   ```bash
   ./setup_coder_templates.sh
   ```

## 🎯 **Success Indicators**

You'll know it's working when you see:
```
[INFO] Checking Python dependencies...
[INFO] Checking environment variables...
[SUCCESS] Environment variables configured

🚀 Coder Template Setup & Validation
=====================================

Choose an option:
1. Show template specifications
2. Show manual creation steps
3. Check existing templates
4. Test workspace functionality
5. Run full validation
6. Exit

Enter your choice (1-6):
```

## 🆘 **Need Help?**

- Check the main [README.md](../README.md)
- See the detailed [CODER_TEMPLATE_SETUP_GUIDE.md](CODER_TEMPLATE_SETUP_GUIDE.md)
- Review the [scripts README.md](README.md)
