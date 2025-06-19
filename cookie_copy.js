// Function to get current timestamp in ISO format
const getISOTimestamp = () => {
    const date = new Date();
    date.setFullYear(date.getFullYear() + 1); // Set expiration to 1 year from now
    return date.toISOString();
};

// Get all cookies as a single string
const cookieString = document.cookie;

// Create the JSON object in the exact format needed
const cookieData = {
    cookies: cookieString,
    user_agent: navigator.userAgent,
    timestamp: getISOTimestamp()
};

// Convert to formatted JSON string
const formattedJson = JSON.stringify(cookieData, null, 2);

// Copy to clipboard
copy(formattedJson);

// Also display in console
console.log("✅ Cookies copied to clipboard in correct format:");
console.log(formattedJson); 