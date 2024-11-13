const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

// Homomorphic Addition Function (for Paillier encryption)
function homomorphicAdd(c1, c2, n, n_sq) {
    return (c1 * c2) % n_sq;  // Paillier Homomorphic Addition: c = c1 * c2 % n^2
}

async function main() {
    const [name, gender, dosageNameCipher, ageCipher, dosageCipher, priceCipher, n] = process.argv.slice(2);

    // Parse n to BigInt
    const nBigInt = BigInt(n);
    const n_sq = nBigInt * nBigInt;  // Calculate n^2

    // Insert data into PharmacyData
    const pharmacyData = await prisma.pharmacyData.create({
        data: {
            name: name,
            gender: gender,
            dosageName: dosageNameCipher,
            age: ageCipher,
            dosage: dosageCipher,
            price: priceCipher
        }
    });

    console.log('Data inserted into PharmacyData');

    // Retrieve the total price stored in the database for the user
    const totalPriceRecord = await prisma.totalPrice.findUnique({
        where: { name: name }  // Find the record by name
    });

    // Extract the encrypted price and perform homomorphic addition
    const encryptedPrice = BigInt(priceCipher);  // Use BigInt for handling large integers in JavaScript

    let totalPrice;
    if (totalPriceRecord) {
        // Perform homomorphic addition of the existing total price and the new encrypted price
        const existingTotalPrice = BigInt(totalPriceRecord.totalPrice);
        const encryptedTotalPrice = homomorphicAdd(existingTotalPrice, encryptedPrice, nBigInt, n_sq);
        totalPrice = encryptedTotalPrice.toString();
    } else {
        totalPrice = encryptedPrice.toString();  // First entry, use the price as it is
    }

    // Store the new total price and user name in the TotalPrice table
    await prisma.totalPrice.upsert({
        where: { name: name },  // Use 'name' as the unique identifier
        update: {
            totalPrice: totalPrice,
            name: name,
            n: nBigInt.toString(),  // Store the 'n' value for future operations
            n_sq: n_sq.toString()  // Store the 'n^2' value for future operations
        },
        create: {
            totalPrice: totalPrice,
            name: name,  // Store the user's name when creating the record
            n: nBigInt.toString(),  // Store the 'n' value
            n_sq: n_sq.toString()  // Store the 'n^2' value
        }
    });

    console.log('Total Price and User Name updated in TotalPrice table');
    await prisma.$disconnect();
}

main().catch((e) => {
    console.error(e);
    prisma.$disconnect();
    process.exit(1);
});
