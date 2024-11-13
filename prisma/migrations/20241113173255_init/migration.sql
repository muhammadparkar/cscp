-- CreateTable
CREATE TABLE "PharmacyData" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "gender" TEXT NOT NULL,
    "dosageName" TEXT NOT NULL,
    "age" TEXT NOT NULL,
    "dosage" TEXT NOT NULL,
    "price" TEXT NOT NULL,

    CONSTRAINT "PharmacyData_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TotalPrice" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "totalPrice" TEXT NOT NULL,
    "n" TEXT NOT NULL,
    "n_sq" TEXT NOT NULL,

    CONSTRAINT "TotalPrice_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "TotalPrice_name_key" ON "TotalPrice"("name");
