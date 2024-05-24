module.exports = {
    languageOptions: {
        ecmaVersion: 2023,
        sourceType: "module",
        globals: {
            window: "readonly",
            document: "readonly",
            jQuery: "writable", 
            $: "writable"
        }
    },
    rules: {
        indent: ["error", 4],
        quotes: ["error", "double"],
        semi: ["error", "always"],
        "no-unused-vars": ["warn"],
        "no-undef": ["error"],
        "eqeqeq": ["error", "always"]
    }
};
