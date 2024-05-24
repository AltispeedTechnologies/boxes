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
        "eqeqeq": ["error", "always"],
        "no-trailing-spaces": ["error"],
        "space-infix-ops": ["error"],
        "no-multi-spaces": ["error", { ignoreEOLComments: false }],
        "space-before-blocks": ["error"]
    }
};
